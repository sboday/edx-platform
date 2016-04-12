;(function (define) {
    'use strict';

    define([
        'js/learner_dashboard/views/collection_list_view',
        'js/learner_dashboard/views/sidebar_view',
        'js/learner_dashboard/views/certificate_view',
        'js/learner_dashboard/collections/certificate_collection'
    ],
    function (
            CollectionListView,
            SidebarView,
            CertificateView,
            CertificateCollection
        ) {
        return function (options) {

            new SidebarView({
                el: '.sidebar',
                context: options
            }).render();

            new CollectionListView({
                el: '.certificate-container',
                childView: CertificateView,
                collection: new CertificateCollection(options.certificatesData)
            }).render();
        };
    });
}).call(this, define || RequireJS.define);
