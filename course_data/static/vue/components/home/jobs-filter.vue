<template>
  <div class="mt-4 mb-4"> 
    <b-card class="p-3 bg-light mb-4">
      <b-form inline>
        <label class="mr-2">Week</label>
        <b-form-select class="mr-2" id="weeks" name="week" v-model="selected_week" @change="changeWeek($event)">
          <b-form-select-option v-for="week in weeks" :key="week.id" :value="week.id">{{week.quarter}} {{week.year}}, week {{week.week}}</b-form-select-option>
        </b-form-select>
        <label class="mr-2">Job Type</label>
        <b-form-select class="mr-2" id="jobtypes" name="jobtype"  v-model="filters.job_type">
          <b-form-select-option :value="'all'" selected>all</b-form-select-option>
          <b-form-select-option v-for="jobtype in jobtypes" :key="jobtype.id" :value="jobtype.type">{{jobtype.type}}</b-form-select-option>
        </b-form-select>
      </b-form>
    </b-card>
  </div>
</template>

<script>
import {mapState, mapMutations} from 'vuex';
import dataMixin from '../../mixins/data_mixin';

export default {
  name: 'jobs-filter',
  mixins: [dataMixin],
  computed: {
    ...mapState({
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
    // default to all job types
    this.$store.state.filters.job_type = "all";
  },
  methods: {
    ...mapMutations([
      'addVarToState',
    ]),
  },
};
</script>

<style lang="scss" scoped>
</style>

