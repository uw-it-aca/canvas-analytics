<template>
  <div class="mt-4 mb-4"> 
    <b-card class="p-3 bg-light mb-4">
      <b-form class="mb-4">
        <label class="mr-2">Date Range</label>
        <jobs-range-picker></jobs-range-picker>
      </b-form>
      <b-form inline>
        <label class="mr-2">Job Type</label>
        <b-form-select class="mr-2" id="jobtypes" name="jobtype"  v-model="filters.job_type">
          <b-form-select-option :value="'all'" selected>all</b-form-select-option>
          <b-form-select-option v-for="jobtype in jobtypes" :key="jobtype.id" :value="jobtype.type">{{jobtype.type}}</b-form-select-option>
        </b-form-select>
        <label class="mr-2">Job Status</label>
        <b-form-select class="mr-2" id="jobstatuses" name="jobstatus"  v-model="filters.job_status">
          <b-form-select-option :value="'all'" selected>all</b-form-select-option>
          <b-form-select-option :value="'pending'">pending</b-form-select-option>
          <b-form-select-option :value="'running'">running</b-form-select-option>
          <b-form-select-option :value="'completed'">completed</b-form-select-option>
          <b-form-select-option :value="'failed'">failed</b-form-select-option>
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
      jobtypes: (state) => state.jobtypes,
      filters: (state) => state.filters,
      terms: (state) => state.terms,
    }),
  },
  async created() {
    // default to all job types
    this.$store.commit('setJobType', "all");
    // default to all job statuses
    this.$store.commit('setJobStatus', "all");
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

