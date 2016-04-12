(function (define) {
  'use strict';
  define([
          'backbone',
          'js/learner_dashboard/models/certificate_model'
    ],
    function (Backbone, Certficate) {
      return Backbone.Collection.extend({
          model: Certficate
      });
  });
}).call(this, define || RequireJS.define);
