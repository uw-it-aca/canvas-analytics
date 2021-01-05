<template>
  <div class="mb-4">
    <b-form inline>
        <label class="mr-2">Week</label>
        <b-form-select class="mr-2" id="weeks" name="week" v-model="selected_week" @change="loadWeek($event)">
          <option v-for="week in weeks" :key="week.id" :value="week.id">{{week.quarter}} {{week.year}}, week {{week.week}}</option>
        </b-form-select>
        <label class="mr-2">Job Type</label>
        <b-form-select class="mr-2" id="jobtypes" name="jobtype"  v-model="filters.job_type" @change="filterAllJobs($event)">
          <option :value="'all'">all</option>
          <option v-for="jobtype in jobtypes" :key="jobtype.id" :value="jobtype.type">{{jobtype.type}}</option>
        </b-form-select>
    </b-form>
  </div>
</template>

<script>
import {mapState, mapMutations} from 'vuex';
import dataMixin from '../mixins/data_mixin';

export default {
  name: 'jobs-filter',
  mixins: [dataMixin],
  computed: {
    ...mapState({
      jobs: (state) => state.jobs,
      weeks: (state) => state.weeks,
      jobtypes: (state) => state.jobtypes,
      selected_week: (state) => state.selected_week,
      filters: (state) => state.filters,
    }),
  },
  async created() {
    // load all jobs for specified week
    if (!this.selected_week) {
      // default to first week option if no filter is specified
      this.$store.state.selected_week = this.weeks[0].id;
    }
    this.loadWeek();
  },
  methods: {
    updateURL: function() {
      console.log("UPDATE URL");
    },
    loadWeek: function() {
      this.getJobs({"week_id": this.selected_week})
        .then(response => {
            if (response.data) {
              this.$store.state.jobs = response.data.jobs;
              this.filterAllJobs();
              this.$store.state.isLoading = false;
            }
        })
    },
    filterAllJobs: function() {
      this.$store.state.isLoading = true;
      let _this = this;
      let filteredJobs = [];
      this.jobs.forEach(function (job, index) {
        if (_this._filterEqual(job.job_type, _this.filters.job_type)) {
          filteredJobs.push(job);
        }
      });
      this.$store.state.filteredJobs = filteredJobs;
      setTimeout(function () {
        // timeout needed for boostrap to display loading icon while filtering
        _this.$store.state.isLoading = false;
      }, 0);
      
    },
    _filterEqual: function(field_value, filter_value) {
        if (filter_value== "all") {
          return true;
        } else if (field_value != filter_value) {
          return false;
        }  else {
          return true;
        }
    },
    ...mapMutations([
      'addVarToState',
    ]),
  },
};
</script>

<style lang="scss" scoped>
</style>

