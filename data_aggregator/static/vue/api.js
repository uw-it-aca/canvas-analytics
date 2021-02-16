import {Vue} from './base.js';
import Vuex from 'vuex';

// custom components
import QueryUsage from './components/api/query-usage.vue';
import QueryExamples from './components/api/query-examples.vue';
import QueryParamDescription from './components/api/query-param-description.vue';

Vue.component('api-query-examples', QueryExamples);
Vue.component('api-query-usage', QueryUsage);
Vue.component('api-query-param-description', QueryParamDescription);

import api_store from './vuex/store/api_store.js';

const store = new Vuex.Store({
  state: {
    // data set on load
    pageTitle: "Web Service Documentation",
    csrfToken: document.getElementsByName('csrfmiddlewaretoken')[0].value,
  },
  mutations: {
  },
  modules: {
    'api_store': api_store
  }
});

new Vue({
    el: '#vue_root',
    store: store,
    created: function() {
      document.title = 'Canvas Analytics: ' + store.state['pageTitle'];
      document.getElementById('vue_root').hidden = false;
    },
})
  
