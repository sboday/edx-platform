from django.core.management import CommandError, call_command

from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from contentstore.management.commands.dump_to_neo4j import ModuleStoreSerializer
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.django import modulestore
import tempfile
import shutil
import os
import csv
import ddt

BLOCK_TYPES = [
    ('about', 1),
    ('course', 1),
    ('chapter', 1),
    ('sequential', 1),
    ('vertical', 1),
    ('html', 1),
    ('problem', 1),
    ('video', 2),
]

@ddt.ddt
class TestModuleStoreSerializer(SharedModuleStoreTestCase):

    @classmethod
    def setUpClass(cls):
        super(TestModuleStoreSerializer, cls).setUpClass()
        cls.course = CourseFactory.create()
        cls.chapter = ItemFactory.create(parent=cls.course, category='chapter')
        cls.sequential = ItemFactory.create(parent=cls.chapter, category='sequential')
        cls.vertical = ItemFactory.create(parent=cls.sequential, category='vertical')
        cls.html = ItemFactory.create(parent=cls.vertical, category='html')
        cls.problem = ItemFactory.create(parent=cls.vertical, category='problem')
        cls.video = ItemFactory.create(parent=cls.vertical, category='video')
        cls.video2 = ItemFactory.create(parent=cls.vertical, category='video')

    def setUp(self):
        self.csv_dir = tempfile.mkdtemp("csv")
        self.neo4j_root = tempfile.mkdtemp("neo4j")

        # Clean temp directories
        self.addCleanup(shutil.rmtree, self.csv_dir)
        self.addCleanup(shutil.rmtree, self.neo4j_root)

    def test_serialize_items(self):
        # test that the serialize_items method works as expected
        modulestore_serializer = ModuleStoreSerializer(self.csv_dir, self.neo4j_root)
        items = modulestore().get_items(self.course.id)
        blocks_by_type = modulestore_serializer.serialize_items(items, self.course.id)
        self.assertItemsEqual(
            [(block_type, len(blocks)) for (block_type, blocks) in blocks_by_type.iteritems()],
            BLOCK_TYPES
        )
        # one course
        self.assertEqual(len(blocks_by_type['course']), 1)
        serialized_course = blocks_by_type['course'][0]
        # that course has the correct fields set on it
        self.assertEqual(serialized_course['course_key'], unicode(self.course.id))
        self.assertFalse(serialized_course['self_paced'])

    def test_csvs_written(self):
        call_command(
            'dump_to_neo4j', csv_dir=self.csv_dir, neo4j_root=self.neo4j_root
        )
        self.assertItemsEqual(
            os.listdir(self.csv_dir),
            [block_type + ".csv" for (block_type, __) in BLOCK_TYPES] + ['relationships.csv']
        )

    @ddt.data(*BLOCK_TYPES)
    @ddt.unpack
    def test_block_csv(self, block_type, expected_number):
        """
        Tests that we only find the expected number of each item in each csv
        """
        call_command(
            'dump_to_neo4j', csv_dir=self.csv_dir, neo4j_root=self.neo4j_root
        )
        filename = self.csv_dir + "/{block_type}.csv".format(block_type=block_type)
        with open(filename) as block_type_csvfile:
            rows = list(csv.reader(block_type_csvfile))

        header = rows[0]
        # assert the first header is the item's label
        self.assertEqual(header[0], "type:LABEL")
        # assert that the id is appropriately set
        self.assertIn("location:ID", header)

        # assert this is the expected number of of items
        body = rows[1:]
        self.assertEqual(len(body), expected_number)

        # assert that the label is the block type
        for row in body:
            self.assertEqual(row[0], block_type)

    def test_relationship_csv(self):
        """
        Tests that the relationship csv looks like it is supposed to.
        """
        call_command(
            'dump_to_neo4j', csv_dir=self.csv_dir, neo4j_root=self.neo4j_root
        )
        filename = self.csv_dir + "/relationships.csv"
        with open(filename) as relationships_csvfile:
            rows = list(csv.reader(relationships_csvfile))

        self.assertEqual(len(rows), 8)
        header = rows[0]
        self.assertEqual(header, [':START_ID', ':END_ID'])
        body = rows[1:]
        self.assertItemsEqual(body, [
            [unicode(self.course.location), unicode(self.chapter.location)],
            [unicode(self.chapter.location), unicode(self.sequential.location)],
            [unicode(self.sequential.location), unicode(self.vertical.location)],
            [unicode(self.vertical.location), unicode(self.html.location)],
            [unicode(self.vertical.location), unicode(self.problem.location)],
            [unicode(self.vertical.location), unicode(self.video.location)],
            [unicode(self.vertical.location), unicode(self.video2.location)],
        ])

    def test_command_idempotent(self):
        """
        Tests that calling the command twice produces the same results
        """
        call_command(
            'dump_to_neo4j', csv_dir=self.csv_dir, neo4j_root=self.neo4j_root
        )
        lengths_of_csvs = {}
        for filename in os.listdir(self.csv_dir):
            filename = os.path.abspath(os.path.join(self.csv_dir, filename))
            with open(filename) as f:
                lengths_of_csvs[filename] = len(f.readlines())

        call_command(
            'dump_to_neo4j', csv_dir=self.csv_dir, neo4j_root=self.neo4j_root
        )
        lengths_of_csvs_2 = {}
        for filename in os.listdir(self.csv_dir):
            filename = os.path.abspath(os.path.join(self.csv_dir, filename))
            with open(filename) as f:
                lengths_of_csvs_2[filename] = len(f.readlines())

        self.assertEqual(lengths_of_csvs, lengths_of_csvs_2)

