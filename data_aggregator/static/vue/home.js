import {Vue} from './base.js';
import Vuex from 'vuex';
import axios from 'axios';

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
    // data set on load
    pageTitle: "Home",
    csrfToken: document.getElementsByName('csrfmiddlewaretoken')[0].value,
    getJobsAjaxRequest: null,
    terms: JSON.parse(document.getElementById('terms').innerHTML), // job terms loaded on page load
    jobTypes: JSON.parse(document.getElementById('jobtypes').innerHTML), // job types loaded on page load
    jobRanges: JSON.parse(document.getElementById('job_ranges').innerHTML),
    // loading state
    isLoading: false, // toggles table loading indicator
    // data returned on each refresh
    jobs: [], // master list of jobs
    totalJobs: 0,
    // data filters
    perPage: 250,
    currPage: 1,
    sortBy: 'status',
    sortDesc: true,
    selectedDateRange: {
      startDate: null,
      endDate: null,
    },
    jobType: [],
    jobStatus: [],
  },
  mutations: {
    setGetJobsAjaxRequest(state, value) {
      state.getJobsAjaxRequest = value;
    },
    setLoading(state, value) {
      state.isLoading = value;
    },
    setSelectedDateRange(state, value) {
      state.selectedDateRange = value;
    },
    setJobs(state, value) {
      state.jobs = value;
    },
    setTotalJobs(state, value) {
      state.totalJobs = value;
    },
    setJobType(state, value) {
      state.jobType = value;
    },
    setJobStatus(state, value) {
      state.jobStatus = value;
    },
    setCurrPage(state, value) {
      state.currPage = value;
    },
    setPerPage(state, value) {
      state.perPage = value;
    },
    setSortBy(state, value) {
      state.sortBy = value;
    },
    setSortDesc(state, value) {
      state.sortDesc = value;
    },
    setSelectedDateRange(state, value) {
      state.selectedDateRange = value;
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
      refreshTime: 5,
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
      selectedDateRange: (state) => state.selectedDateRange,
      perPage: (state) => state.perPage,
      currPage: (state) => state.currPage,
      sortBy: (state) => state.sortBy,
      sortDesc: (state) => state.sortDesc,
      jobs: (state) => state.jobs,
      jobType: (state) => state.jobType,
      jobStatus: (state) => state.jobStatus,
    }),
    selectedJobs: function() {
      return this.jobs.filter(
          job => (job.selected == true)
      );
    },
    refreshTriggers: function() {
      // refresh if any of these change 
      return this.selectedDateRange, this.currPage, this.perPage,
        this.sortBy, this.sortDesc, this.jobType, this.jobStatus;
    }
  },
  watch: {
    refreshTriggers: function() {
      this.changeSelection()
    },
  },
  methods: {
    refreshJobs: function() {
      let promise = this.getJobs({
        "dateRange": this.selectedDateRange,
        "perPage": this.perPage,
        "currPage": this.currPage,
        "sortBy": this.sortBy,
        "sortDesc": this.sortDesc,
        "jobType": this.jobType,
        "jobStatus": this.jobStatus
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
          this.$store.commit('setTotalJobs',  response.data.total_jobs);
          this.$store.commit('setJobs', response.data.jobs);
        }
      })
      .catch((error) => {
        if (axios.isCancel(error)) {
            console.log("POST request canceled as a new request was made.");
        }
      }).finally(() => {
        // reset axios cancel token
        this.$store.commit('setGetJobsAjaxRequest', null); 
      });
      return promise;
    },
    changeSelection: function() {
      // load a new week
      this.$store.commit('setLoading', true);
      let _this = this;
      this.refreshJobs().finally(response => {
        _this.$store.commit('setLoading', false);
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
