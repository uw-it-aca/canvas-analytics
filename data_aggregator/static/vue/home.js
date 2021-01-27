import {Vue} from './base.js';
import Vuex from 'vuex';

// custom components
import JobsTable from './components/home/jobs-table.vue';
import JobsFilter from './components/home/jobs-filter.vue';
import JobsRangePicker from './components/home/jobs-range-picker.vue';

Vue.component('jobs-table', JobsTable);
Vue.component('jobs-filter', JobsFilter);
Vue.component('jobs-range-picker', JobsRangePicker);

// date range picker component - https://innologica.github.io/vue2-daterange-picker/
import DateRangePicker from 'vue2-daterange-picker';
import 'vue2-daterange-picker/dist/vue2-daterange-picker.css';
Vue.component('date-range-picker', DateRangePicker);

// multiselect component - https://vue-multiselect.js.org/
import Multiselect from 'vue-multiselect'
import 'vue-multiselect/dist/vue-multiselect.min.css';
Vue.component('multiselect', Multiselect)

// stores
import home_store from './vuex/store/home_store.js';

const store = new Vuex.Store({
  state: {
    pageTitle: "Home",
    csrfToken: document.getElementsByName('csrfmiddlewaretoken')[0].value,
    jobs: [], // master list of jobs
    terms: JSON.parse(document.getElementById('terms').innerHTML), // job terms loaded on page load
    jobtypes: JSON.parse(document.getElementById('jobtypes').innerHTML), // job types loaded on page load
    job_ranges: JSON.parse(document.getElementById('job_ranges').innerHTML),
    isLoading: false, // toggles table loading indicator
    selected_date_range: {
      startDate: null,
      endDate: null,
    },
    filters: {
      job_type: [],
      job_status: [],
    }
  },
  mutations: {
    setJobs(state, value) {
      state.jobs = value;
    },
    setJobType(state, value) {
      state.filters.job_type = value;
    },
    setJobStatus(state, value) {
      state.filters.job_status = value;
    },
    setLoading(state, value) {
      state.isLoading = value;
    },
    setSelectedDateRange(state, value) {
      state.selected_date_range = value;
    },
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
  data: function() {
    return {
      refreshTime: 15,
      refreshTimer: null,
    }
  },
  created: function() {
    document.title = 'Canvas Data Aggregator Jobs: ' + store.state['pageTitle'];
    document.getElementById('vue_root').hidden = false;
    this.refreshTimer = setInterval(this.refreshJobs, this.refreshTime * 1000);
  },
  computed: {
    ...mapState({
      selected_date_range: (state) => state.selected_date_range,
      jobs: (state) => state.jobs,
      filters: (state) => state.filters,
    }),
    selectedJobs: function() {
      return this.jobs.filter(
          job => (job.selected == true)
      );
    },
    filteredJobs: function() {
      this.$store.commit('setLoading', true);
      let filteredJobs = [];
      let _this = this;
      this.jobs.forEach(function (job, index) {
        if (_this._filterList(job.job_type, _this.filters.job_type) &&
          _this._filterList(_this.getStatus(job), _this.filters.job_status)
        ) {
          filteredJobs.push(job);
        }
      });
      this.$store.commit('setLoading', false);
      return filteredJobs;
    }
  },
  watch: {
    selected_date_range: function() {
      this.changeSelection();
    },
  },
  methods: {
    _filterEqual: function(field_value, filter_value) {
        if (filter_value == "all") {
          return true;
        } else if (field_value != filter_value) {
          return false;
        }  else {
          return true;
        }
    },
    _filterList: function(field_value, filter_value) {
      if (filter_value.length == 0) {
        return true;
      } else if (!filter_value.includes(field_value)) {
        return false;
      }  else {
        return true;
      }
  },
    refreshJobs: function() {
      let promise = this.getJobs({
        "date_range": this.selected_date_range,
      })
      .then(response => {
        if (response.data) {
          // we need to reset all selected ids on every refresh
          let _this = this;
          let selectedJobIds = this.selectedJobs.map(job => job.id)
          response.data.jobs.forEach(function (job, index) {
            if(selectedJobIds.includes(job.id)) {
              job.selected = true;
            }
          });
          this.$store.commit('setJobs', response.data.jobs);
        }
      });
      return promise;
    },
    changeSelection: function() {
      // load a new week
      this.$store.commit('setLoading', true);
      this.refreshJobs().then(response => {
        this.$store.commit('setLoading', false);
      })
    },
    ...mapMutations([
      'addVarToState',
    ]),
  },
  beforeDestroy () {
    clearInterval(this.refreshTimer);
  },
})
