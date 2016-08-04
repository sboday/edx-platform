"""
Grades related signals.
"""
from django.dispatch import receiver, Signal
from logging import getLogger
from student.models import user_by_anonymous_id
from submissions.models import score_set, score_reset


log = getLogger(__name__)


# Signal that indicates that a user's score for a problem has been updated.
# This signal is generated when a scoring event occurs either within the core
# platform or in the Submissions module. Note that this signal will be triggered
# regardless of the new and previous values of the score (i.e. it may be the
# case that this signal is generated when a user re-attempts a problem but
# receives the same score).
SCORE_CHANGED = Signal(
    providing_args=[
        'points_possible',  # Maximum score available for the exercise
        'points_earned',   # Score obtained by the user
        'user_id',  # Integer User ID
        'course_id',  # Unicode string representing the course
        'usage_id'  # Unicode string indicating the courseware instance
    ]
)


@receiver(score_set)
def submissions_score_set_handler(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Consume the score_set signal defined in the Submissions API, and convert it
    to a SCORE_CHANGED signal defined in this module. Converts the unicode keys
    for user, course and item into the standard representation for the
    SCORE_CHANGED signal.

    This method expects that the kwargs dictionary will contain the following
    entries (See the definition of score_set):
      - 'points_possible': integer,
      - 'points_earned': integer,
      - 'anonymous_user_id': unicode,
      - 'course_id': unicode,
      - 'item_id': unicode
    """
    points_possible = kwargs.get('points_possible', None)
    points_earned = kwargs.get('points_earned', None)
    course_id = kwargs.get('course_id', None)
    usage_id = kwargs.get('item_id', None)
    user = None
    if 'anonymous_user_id' in kwargs:
        user = user_by_anonymous_id(kwargs.get('anonymous_user_id'))

    # If any of the kwargs were missing, at least one of the following values
    # will be None.
    if all((user, points_possible, points_earned, course_id, usage_id)):
        SCORE_CHANGED.send(
            sender=None,
            points_possible=points_possible,
            points_earned=points_earned,
            user_id=user.id,
            course_id=course_id,
            usage_id=usage_id
        )
    else:
        log.exception(
            u"Failed to process score_set signal from Submissions API. "
            "points_possible: %s, points_earned: %s, user: %s, course_id: %s, "
            "usage_id: %s", points_possible, points_earned, user, course_id, usage_id
        )


@receiver(score_reset)
def submissions_score_reset_handler(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Consume the score_reset signal defined in the Submissions API, and convert
    it to a SCORE_CHANGED signal indicating that the score has been set to 0/0.
    Converts the unicode keys for user, course and item into the standard
    representation for the SCORE_CHANGED signal.

    This method expects that the kwargs dictionary will contain the following
    entries (See the definition of score_reset):
      - 'anonymous_user_id': unicode,
      - 'course_id': unicode,
      - 'item_id': unicode
    """
    course_id = kwargs.get('course_id', None)
    usage_id = kwargs.get('item_id', None)
    user = None
    if 'anonymous_user_id' in kwargs:
        user = user_by_anonymous_id(kwargs.get('anonymous_user_id'))

    # If any of the kwargs were missing, at least one of the following values
    # will be None.
    if all((user, course_id, usage_id)):
        SCORE_CHANGED.send(
            sender=None,
            points_possible=0,
            points_earned=0,
            user_id=user.id,
            course_id=course_id,
            usage_id=usage_id
        )
    else:
        log.exception(
            u"Failed to process score_reset signal from Submissions API. "
            "user: %s, course_id: %s, usage_id: %s", user, course_id, usage_id
        )
