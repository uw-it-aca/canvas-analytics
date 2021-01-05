import {Vue, vueConf} from './base.js';

// components
import JobsTable from './components/jobs-table.vue';
import JobsFilter from './components/jobs-filter.vue';

// stores
import jobs_store from './vuex/store/jobs_store.js';

vueConf.store.registerModule('jobs_store', jobs_store);

vueConf.store.commit('addVarToState', {
    name: 'pageTitle',
    value: 'Home',
  });

Vue.component('jobs-table', JobsTable);
Vue.component('jobs-filter', JobsFilter);

new Vue({
  ...vueConf,
})
