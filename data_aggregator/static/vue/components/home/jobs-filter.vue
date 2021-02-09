<template>
  <b-card class="p-3 mb-4">
    <b-container fluid>
      <b-row>
        <b-col xs="12">
          <b-form class="mb-2">
            <label class="mr-2">Active job bounds</label>
            <active-range-picker></active-range-picker>
          </b-form>
          <p>
            <ul>
              <li><small>Results limited to jobs with an active date range that interersects {{activeDateRange.startDate | iso_date}} - {{activeDateRange.endDate | iso_date}}</small></li>
            </ul>
          </p>
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

