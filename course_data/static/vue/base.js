import Vue from 'vue';
import Vuex from 'vuex';

import { BootstrapVue, BootstrapVueIcons } from 'bootstrap-vue'

// Import Bootstrap an BootstrapVue CSS files (order is important)
import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue/dist/bootstrap-vue.css'

// Make BootstrapVue available throughout project
Vue.use(BootstrapVue);
Vue.use(BootstrapVueIcons);

// vuex
Vue.use(Vuex);

Vue.config.devtools = true;

const store = new Vuex.Store({
  state: {
    csrfToken: document.getElementsByName('csrfmiddlewaretoken')[0].value,
    weeks: JSON.parse(document.getElementById('weeks').innerHTML),
    jobtypes: JSON.parse(document.getElementById('jobtypes').innerHTML),
    isLoading: false,
    jobs: [],
    filteredJobs: [],
    selected_week: null,
    filters: {
      job_type: "all",
    }
  },
  mutations: {
    addVarToState(state, {name, value}) {
      state[name] = value;
    },
  },
});

Vue.config.devtools = true;

const vueConf = {
  el: '#vue_root',
  created: function() {
    document.title = 'Course-Data: ' + store.state['pageTitle'];
    document.getElementById('vue_root').hidden = false;
  },
  store: store,
};

export {Vue, vueConf};
