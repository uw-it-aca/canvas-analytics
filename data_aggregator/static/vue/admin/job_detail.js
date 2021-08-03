import {Vue} from './admin_base.js';
import Vuex from 'vuex';

// custom components
import JobDescription from '../components/admin/job-description.vue';
import JobRelatedData from '../components/admin/job-related-data.vue';

Vue.component('job-description', JobDescription);
Vue.component('job-related-data', JobRelatedData);

// stores
import admin_store from '../vuex/store/admin_store.js';

const store = new Vuex.Store({
  state: {
    // data set on load
    pageTitle: "Job Detail Admin",
    job: JSON.parse(document.getElementById('object').innerHTML),
    related_objects: JSON.parse(document.getElementById('related_objects').innerHTML),
  },
  mutations: {
  },
  modules: {
    'admin_store': admin_store
  }
});

// initialize root component
import {mapState} from 'vuex';

new Vue({
  el: '#vue_root',
  store: store,
  data: function() {
    return {};
  },
  created: function() {
    document.title = 'Canvas Analytics: ' + store.state.pageTitle;
    document.getElementById('vue_root').hidden = false;
  },
  computed: {
    ...mapState({
    }),
  },
});
