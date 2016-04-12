;(function (define) {
    'use strict';

    define(['backbone',
            'jquery',
            'underscore',
            'gettext',
            'text!../../../templates/learner_dashboard/certificate.underscore'
           ],
         function(
             Backbone,
             $,
             _,
             gettext,
             certificateTpl
         ) {
            return Backbone.View.extend({
                className: '',
                tpl: _.template(certificateTpl),
                initialize: function() {
                    this.render();
                },
                render: function() {
                    var templated = this.tpl(this.model.toJSON());
                    this.$el.append(templated);
                }
            });
        }
    );
}).call(this, define || RequireJS.define);
