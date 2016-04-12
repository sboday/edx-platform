;(function (define) {
    'use strict';

    define(['backbone',
            'jquery',
            'underscore',
            'gettext',
            'text!../../../templates/learner_dashboard/explore_new_programs.underscore'
           ],
         function(
             Backbone,
             $,
             _,
             gettext,
             exploreTpl
         ) {
            return Backbone.View.extend({
                el: '.program-advertise',

                tpl: _.template(exploreTpl),

                events: {
                    'click .js-explore-programs': 'linkClicked'
                },

                initialize: function(data) {
                    this.context = data.context;
                    this.$parentEl = $(this.parentEl);

                    if (this.context.xseriesUrl){
                        // Only render if there is an XSeries link
                        this.render();
                    } else {
                        /**
                         *  If not rendering remove el because
                         *  styles are applied to the wrapper
                         */
                        this.remove();
                    }
                },

                render: function() {
                    this.$el.html(this.tpl(this.context));  
                },

                linkClicked: function() {
                    analytics.track('edx.bi.programs_listing.find_xseries_link.clicked', {
                        category: 'programs_listing'
                    });
                }
            });
        }
    );
}).call(this, define || RequireJS.define);
