;(function (define) {
    'use strict';

    define([
        'js/learner_dashboard/views/collection_list_view',
//        'js/learner_dashboard/views/sidebar_view',
        'js/learner_dashboard/views/program_card_view',
        'js/learner_dashboard/collections/program_collection'
    ],
    function (CollectionListView, ProgramCardView, ProgramCollection) {
        return function (options) {
            new CollectionListView({
                el: '.program-cards-container',
                childView: ProgramCardView,
                collection: new ProgramCollection(options.programsData)
            }).render();
        };
    });
}).call(this, define || RequireJS.define);
