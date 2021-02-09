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
    refreshTime: 5,
    // loading state
    isLoading: false, // toggles table loading indicator
    // data returned on each refresh
    jobs: [], // master list of jobs
    totalJobs: 0,
    // data filters
    perPage: 250,
    currPage: 1,
    sortBy: 'status',
    sortDesc: false,
    selectedDateRange: {
      startDate: null,
      endDate: null,
    },
    jobType: [],
    jobStatus: [],
    selectedJobRunningDateRange: {
      startDate: null,
      endDate: null,
    }
  },
  mutations: {
    setRefreshTime(state, value) {
      state.refreshTime = value;
    },
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
    setRangeStartDate(state, value) {
      state.selectedDateRange.startDate = value;
    },
    setRangeEndDate(state, value) {
      state.selectedDateRange.endDate = value;
    },
    setSelectedJobRunningDateRange(state, value) {
      state.selectedJobRunningDateRange = value;
    },
    setJobRunningStartDate(state, value) {
      state.selectedJobRunningDateRange.startDate = value;
    },
    setJobRunningEndDate(state, value) {
      state.selectedJobRunningDateRange.endDate = value;
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
import {parseIsoDateStr, toIsoDateStr} from "../js/utilities.js";
import {mapState} from 'vuex';

new Vue({
  el: '#vue_root',
  store: store,
  mixins: [dataMixin, utilitiesMixin],
  data: function() {
    return {
      refreshTimer: null,
    }
  },
  beforeCreate: function () {
    // parse url arguments when app is loaded 
    let hash = window.location.hash;

    hash = hash.substring(hash.indexOf("#")+1); // ignore # symbol
    
    // convert the hash string into a dictionary
    try {
      hash = hash?JSON.parse('{"' + hash.replace(/&/g, '","').replace(/=/g,'":"') + '"}',
                function(key, value) { return key===""?value:decodeURIComponent(value) }):{};
    } catch (e) {
      hash = {}; // invalid hash query string
    }

    // update store with values from hash
    if(hash["perPage"]) {
      this.$store.commit('setPerPage',  parseInt(hash["perPage"]));
    }
    if(hash["currPage"]) {
      this.$store.commit('setCurrPage',  parseInt(hash["currPage"]));
    }
    if(hash["sortBy"]) {
      this.$store.commit('setSortBy',  hash["sortBy"]);
    }
    if(hash["sortDesc"]) {
      this.$store.commit('setSortDesc',
                         (hash["sortDesc"].toLowerCase() === 'true'));
    }
    if(hash["startDate"]) {
      let dateStr = toIsoDateStr(parseIsoDateStr(hash["startDate"]));
      this.$store.commit('setRangeStartDate', dateStr);
    }
    if(hash["endDate"]) {
      let dateStr = toIsoDateStr(parseIsoDateStr(hash["endDate"]));
      this.$store.commit('setRangeEndDate', dateStr);
    }
    if(hash["jobStartDate"]) {
      let dateStr = toIsoDateStr(parseIsoDateStr(hash["jobStartDate"]));
      this.$store.commit('setJobRunningStartDate', dateStr);
    }

    if(hash["jobEndDate"]) {
      let dateStr = toIsoDateStr(parseIsoDateStr(hash["jobEndDate"]));
      this.$store.commit('setJobRunningEndDate', dateStr);
  }

    if(hash["refreshTime"]) {
      this.$store.commit('setRefreshTime', parseInt(hash["refreshTime"]))
    }
    if(hash["jobType"]) {
      this.$store.commit('setJobType', hash["jobType"].split(','))
    }
    if(hash["jobStatus"]) {
      this.$store.commit('setJobStatus', hash["jobStatus"].split(','))
    }
  },
  created: function() {
    document.title = 'Canvas Data Aggregator Jobs: ' + store.state['pageTitle'];
    document.getElementById('vue_root').hidden = false;
    this.changeSelection() // run without delay and with loading indicators 
    this.refreshTimer = setInterval(this.refreshJobs, this.refreshTime * 1000);
  },
  computed: {
    ...mapState({
      refreshTime: (state) => state.refreshTime,
      selectedDateRange: (state) => state.selectedDateRange,
      selectedJobRunningDateRange: (state) => state.selectedJobRunningDateRange,
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
    selectionChangeTriggers: function() {
      // refresh if any of these change
      return this.selectedDateRange, this.selectedJobRunningDateRange,
        this.currPage, this.perPage, this.sortBy, this.sortDesc, this.jobType,
        this.jobStatus;
    }
  },
  watch: {
    selectionChangeTriggers: function() {
      this.changeSelection();
    },
    refreshTime: function() {
      this.updateURL();
      clearInterval(this.refreshTimer);
      this.refreshTimer = setInterval(this.refreshJobs, this.refreshTime * 1000);
    }
  },
  methods: {
    refreshJobs: function() {
      let promise = this.getJobs({
        "dateRange": {
          "startDate": parseIsoDateStr(this.selectedDateRange.startDate),
          "endDate": parseIsoDateStr(this.selectedDateRange.endDate),
        },
        "jobRunningDateRange": {
          "startDate": parseIsoDateStr(this.selectedJobRunningDateRange.startDate),
          "endDate": parseIsoDateStr(this.selectedJobRunningDateRange.endDate),
        },
        "perPage": this.perPage,
        "currPage": this.currPage,
        "sortBy": this.sortBy,
        "sortDesc": this.sortDesc,
        "jobType": this.jobType,
        "jobStatus": this.jobStatus,
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
      this.updateURL()
      this.$store.commit('setLoading', true);
      let _this = this;
      this.refreshJobs().finally(response => {
        _this.$store.commit('setLoading', false);
      })
    },
    updateURL: function() {
      let params = {};
      params['perPage'] = this.$store.state.perPage;
      params['currPage'] = this.$store.state.currPage;
      params['sortBy'] = this.$store.state.sortBy;
      params['sortDesc'] = this.$store.state.sortDesc;
      params['startDate'] = toIsoDateStr(
        this.$store.state.selectedDateRange.startDate);
      params['endDate'] = toIsoDateStr(
        this.$store.state.selectedDateRange.endDate);
      params['refreshTime'] = this.$store.state.refreshTime;
      if(this.$store.state.jobType.length > 0)
        params['jobType'] = this.$store.state.jobType.join(",");
      if(this.$store.state.jobStatus.length > 0)
        params['jobStatus'] = this.$store.state.jobStatus.join(",");
      if(this.$store.state.selectedJobRunningDateRange.startDate)
        params['jobStartDate'] = toIsoDateStr(
          this.$store.state.selectedJobRunningDateRange.startDate);
      if(this.$store.state.selectedJobRunningDateRange.endDate)
        params['jobEndDate'] = toIsoDateStr(
          this.$store.state.selectedJobRunningDateRange.endDate)
      let queryParams = Object.keys(params).map(function(k) {
        return encodeURIComponent(k) + '=' + encodeURIComponent(params[k])
      }).join('&')
      let url = window.location.href.split("#")[0];
      window.location.replace(url + "#" + decodeURIComponent(queryParams));
    },
  },
  beforeDestroy () {
    clearInterval(this.refreshTimer);
  },
})
