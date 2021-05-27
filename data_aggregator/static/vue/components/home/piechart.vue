<template>
    <GChart
        v-if="chartData"
        type="PieChart"
        :data="chartData"
        :options="chartOptions"
        :settings="{ packages: ['corechart'] }"
    />
</template>

<script>
import {mapState, mapMutations} from 'vuex';
import { GChart } from 'vue-google-charts'

export default {
  name: 'piechart',
  components: {
    GChart
  },
  data: function() {
    return {
      chartOptions: {
        pieHole: 0.4,
        chartArea: {left: '20%', width: '120%', height: '120%'},
        sliceVisibilityThreshold: 0,
        pieSliceTextStyle: {
          color: 'black',
          fontSize: 11
        },
        colors: ['#d4edda', '#eef8b8', '#f8d7da', '#adadad', '#d1ecf1'],
      }
    }
  },
  computed: {
    ...mapState({
        jobsGroupedByStatus: (state) => state.jobsGroupedByStatus,
    }),
    chartData: function() {
        let cd = [];
        cd.push(["Status", "Count"]);
        if (Object.keys(this.jobsGroupedByStatus).length) {
            // get counts per job status
            for (const [jobStatus, count] of 
                    Object.entries(this.jobsGroupedByStatus)) {
                let cd_entry = [jobStatus, count];
                cd.push(cd_entry);
            }
            return cd
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

