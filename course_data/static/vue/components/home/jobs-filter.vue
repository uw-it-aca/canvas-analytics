<template>
  <b-card class="p-3 bg-light mb-4">
    <b-container fluid>
      <b-row>
        <b-col xs="12">
          <b-form>
            <label class="mr-2">Active Job Date Range</label>
            <jobs-range-picker></jobs-range-picker>
          </b-form>
        </b-col>
      </b-row>
    </b-container>
  </b-card>
</template>

<script>
import {mapState, mapMutations} from 'vuex';
import dataMixin from '../../mixins/data_mixin';

export default {
  name: 'jobs-filter',
  mixins: [dataMixin],
  computed: {
    ...mapState({
    }),
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

