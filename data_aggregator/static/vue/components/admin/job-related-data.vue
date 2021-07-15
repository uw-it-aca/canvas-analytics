<template>
<b-container fluid>
  <b-row>
    <p>This job has {{related_objects.length}} related analytics.</p>
  </b-row>
  <b-row v-if="related_objects.length > 0">
    <b-col xs="12" md="5">
      <b-pagination
        v-model="currPage"
        :total-rows="related_objects.length"
        :per-page="perPage"
        aria-controls="related-objects"
        size="sm"
        limit="7"
        first-number
        last-number>
      </b-pagination>
    </b-col>
    <b-col xs="12" md="7">
      <b-form class="d-flex flex-nowrap" inline>
        <label class="ml-2 mr-2">Page Size</label>
        <b-form-select v-model="perPage" id="page-size" name="page-size">
          <b-form-select-option :value="100">100</b-form-select-option>
          <b-form-select-option :value="250">250</b-form-select-option>
          <b-form-select-option :value="500">500</b-form-select-option>
          <b-form-select-option :value="1000">1000</b-form-select-option>
        </b-form-select>
      </b-form>
    </b-col>
  </b-row>
  <b-list-group id="related-objects">
    <b-list-group-item v-for="obj in pagedRelatedObjects" :key="obj.id">{{obj}}</b-list-group-item>
  </b-list-group>
</b-container>
</template>

<script>
import {mapState, mapMutations} from 'vuex';

export default {
  name: 'api-query-param-description',
  data: function() {
    return {
      currPage: 1,
      perPage: 100
    }
  },
  computed: {
    ...mapState({
        job: (state) => state.job,
        related_objects: (state) => state.related_objects,
    }),
    pagedRelatedObjects: {
      get () {
        let start = this.perPage * (this.currPage - 1);
        let end = this.perPage * this.currPage;
        return this.$store.state.related_objects.slice(start, end);
      }
    },
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
