<template>
  <b-card class="p-1 mb-4">
    <b-container fluid>
      <b-row>
        <b-col xs="12">
          <b-form class="mb-2">
            <label class="mr-2">Active job bounds</label>
            <active-range-picker></active-range-picker>
          </b-form>
          <piechart></piechart>
        </b-col>
      </b-row>
    </b-container>
  </b-card>
</template>

<script>
import {mapState, mapMutations} from 'vuex';
import utilitiesMixin from '../../mixins/utilities_mixin';

export default {
  name: 'jobs-filter',
  mixins: [utilitiesMixin],
  computed: {
    ...mapState({
      activeDateRange: (state) => state.activeDateRange,
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

