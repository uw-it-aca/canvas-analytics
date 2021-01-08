import {Vue} from './base.js';
import Vuex from 'vuex';

// components
import JobsTable from './components/home/jobs-table.vue';
import JobsFilter from './components/home/jobs-filter.vue';

Vue.component('jobs-table', JobsTable);
Vue.component('jobs-filter', JobsFilter);

// stores
import home_store from './vuex/store/home_store.js';

const store = new Vuex.Store({
  state: {
    pageTitle: "Home",
    csrfToken: document.getElementsByName('csrfmiddlewaretoken')[0].value,
    jobs: [], // master list of jobs
    weeks: JSON.parse(document.getElementById('weeks').innerHTML), // job weeks loaded on page load
    jobtypes: JSON.parse(document.getElementById('jobtypes').innerHTML), // job types loaded on page load
    isLoading: false, // toggles table loading indicator
    selected_week: null, // selected week to load
    filters: {
      job_type: "",
      job_status: "",
    }
  },
  mutations: {
    addVarToState(state, {name, value}) {
      state[name] = value;
    },
  },
  modules: {
    'home_store': home_store
  }
});

// initializae root component 
import dataMixin from './mixins/data_mixin';
import utilitiesMixin from './mixins/utilities_mixin';
import {mapState, mapMutations} from 'vuex';

new Vue({
  el: '#vue_root',
  store: store,
  mixins: [dataMixin, utilitiesMixin],
  created: function() {
    document.title = 'Canvas Analytics Jobs: ' + store.state['pageTitle'];
    document.getElementById('vue_root').hidden = false;
  },
  computed: {
    ...mapState({
      selected_week: (state) => state.selected_week,
    }),
    filteredJobs: function() {
      this.$store.state.isLoading = true;
      let _this = this;
      let filteredJobs = [];
      this.$store.state.jobs.forEach(function (job, index) {
        if (_this._filterEqual(job.job_type, _this.$store.state.filters.job_type) &&
          _this._filterEqual(_this.getStatus(job), _this.$store.state.filters.job_status)
        ) {
          filteredJobs.push(job);
        }
      });
      setTimeout(function () {
        // timeout needed for bootstrap to display loading icon while filtering
        _this.$store.state.isLoading = false;
      }, 0);
      return filteredJobs;
    }
  },
  watch: {
    selected_week: function() {
      this.changeWeek();
    }
  },
  methods: {
    _filterEqual: function(field_value, filter_value) {
        if (filter_value== "all") {
          return true;
        } else if (field_value != filter_value) {
          return false;
        }  else {
          return true;
        }
    },
    changeWeek: function() {
      // load a new week
      this.$store.state.isLoading = true;
      this.getJobs({"week_id": this.selected_week})
        .then(response => {
            if (response.data) {
              this.$store.state.jobs = response.data.jobs;
              this.$store.state.isLoading = false;
            }
      })
    },
    ...mapMutations([
      'addVarToState',
    ]),
  },
})
