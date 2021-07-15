import {Vue} from '../base.js';
import Vuex from 'vuex';
import axios from 'axios';

// custom components
import ActiveRangePicker from '../components/admin/active-range-picker.vue';
import JobsTable from '../components/admin/jobs-table.vue';
import JobsFilter from '../components/admin/jobs-filter.vue';
import Chart from '../components/admin/chart.vue';
import TimeDifferenceWidget from '../components/admin/widgets/time-difference-widget.vue';
import TimeWidget from '../components/admin/widgets/time-widget.vue';

Vue.component('jobs-table', JobsTable);
Vue.component('jobs-filter', JobsFilter);
Vue.component('active-range-picker', ActiveRangePicker);
Vue.component('chart', Chart);
Vue.component('time-widget', TimeWidget);
Vue.component('time-difference-widget', TimeDifferenceWidget);

// date range picker component - https://innologica.github.io/vue2-daterange-picker/
import DateRangePicker from 'vue2-daterange-picker';
import 'vue2-daterange-picker/dist/vue2-daterange-picker.css';
Vue.component('date-range-picker', DateRangePicker);

// multiselect component - https://vue-multiselect.js.org/
import Multiselect from 'vue-multiselect'
import 'vue-multiselect/dist/vue-multiselect.min.css';
Vue.component('multiselect', Multiselect)

// stores
import admin_store from '../vuex/store/admin_store.js';

const store = new Vuex.Store({
  state: {
    // data set on load
    pageTitle: "Jobs Admin",
    csrfToken: document.getElementsByName('csrfmiddlewaretoken')[0].value,
    getJobsAjaxRequest: null,
    terms: JSON.parse(document.getElementById('terms').innerHTML), // job terms loaded on page load
    jobTypes: JSON.parse(document.getElementById('jobtypes').innerHTML), // job types loaded on page load
    jobRanges: JSON.parse(document.getElementById('job_ranges').innerHTML),
    refreshTime: 30,
    // loading state
    isLoading: false, // toggles table loading indicator
    // data returned on each refresh
    jobs: [], // master list of jobs
    totalJobs: 0,
    // data returned by jobs chart data endpoint
    jobsGroupedByStatus: {},
    // data filters
    perPage: 250,
    currPage: 1,
    sortBy: 'job_type',
    sortDesc: false,
    jobType: [],
    jobStatus: [],
    activeDateRange: {
      startDate: null,
      endDate: null,
    },
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
    setActiveDateRange(state, value) {
      state.activeDateRange = value;
    },
    setJobs(state, value) {
      state.jobs = value;
    },
    setTotalJobs(state, value) {
      state.totalJobs = value;
    },
    setJobsGroupedByStatus(state, value) {
      state.jobsGroupedByStatus = value;
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
    setActiveDateRange(state, value) {
      state.activeDateRange = value;
    },
    setActiveRangeStartDate(state, value) {
      state.activeDateRange.startDate = value;
    },
    setActiveRangeEndDate(state, value) {
      state.activeDateRange.endDate = value;
    },
    addVarToState(state, {name, value}) {
      state[name] = value;
    },
  },
  modules: {
    'admin_store': admin_store
  }
});

// initialize root component 
import dataMixin from '../mixins/data_mixin';
import utilitiesMixin from '../mixins/utilities_mixin';
import utilities from "../../js/utilities.js";
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
      let dateStr = utilities.toIsoDateStr(utilities.parseIsoDateStr(hash["startDate"]));
      this.$store.commit('setActiveRangeStartDate', dateStr);
    }
    if(hash["endDate"]) {
      let dateStr = utilities.toIsoDateStr(utilities.parseIsoDateStr(hash["endDate"]));
      this.$store.commit('setActiveRangeEndDate', dateStr);
    }
    if(hash["jobStartDate"]) {
      let dateStr = utilities.toIsoDateStr(utilities.parseIsoDateStr(hash["jobStartDate"]));
      this.$store.commit('setJobRangeStartDate', dateStr);
    }

    if(hash["jobEndDate"]) {
      let dateStr = utilities.toIsoDateStr(utilities.parseIsoDateStr(hash["jobEndDate"]));
      this.$store.commit('setJobRangeEndDate', dateStr);
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
    document.title = 'Canvas Analytics: ' + store.state['pageTitle'];
    document.getElementById('vue_root').hidden = false;
    this.changeSelection() // run without delay and with loading indicators 
    this.refreshTimer = setInterval(this.refreshJobs, this.refreshTime * 1000);
    this.refreshTimer = setInterval(this.refreshJobsGroupedByStatus,
                                    this.refreshTime * 1000);
  },
  computed: {
    ...mapState({
      refreshTime: (state) => state.refreshTime,
      activeDateRange: (state) => state.activeDateRange,
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
      return this.activeDateRange,
        this.currPage, this.perPage, this.sortBy, this.sortDesc, this.jobType,
        this.jobStatus;
    },
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
        "activeDateRange": {
          "startDate": utilities.parseIsoDateStr(this.activeDateRange.startDate),
          "endDate": utilities.parseIsoDateStr(this.activeDateRange.endDate),
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
    refreshJobsGroupedByStatus: function() {
      let _this = this;
      let promise = this.getJobsChartData({
        "activeDateRange": {
          "startDate": utilities.parseIsoDateStr(this.activeDateRange.startDate),
          "endDate": utilities.parseIsoDateStr(this.activeDateRange.endDate),
        },
        "jobType": this.jobType,
      })
      .then(response => {
        if (response.data) {
          // we need to reset all selected ids on every refresh
          _this.$store.commit('setJobsGroupedByStatus', response.data);
        }
      })
      return promise;
    },
    changeSelection: function() {
      this.updateURL()
      this.$store.commit('setLoading', true);
      let _this = this;
      this.refreshJobsGroupedByStatus();
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
      params['startDate'] = utilities.toIsoDateStr(
        this.$store.state.activeDateRange.startDate);
      params['endDate'] = utilities.toIsoDateStr(
        this.$store.state.activeDateRange.endDate);
      params['refreshTime'] = this.$store.state.refreshTime;
      if(this.$store.state.jobType.length > 0)
        params['jobType'] = this.$store.state.jobType.join(",");
      if(this.$store.state.jobStatus.length > 0)
        params['jobStatus'] = this.$store.state.jobStatus.join(",");
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
