<template>
      <div>
        <b-form class="d-flex flex-nowrap" inline>
            <label class="mr-2">Chart Type</label>
            <b-form-select v-model="selectedChartType" :options="chartTypes">
            </b-form-select>
        </b-form>
        <GChart
          v-if="chartData"
          :type="selectedChartType"
          :data="chartData"
          :options="chartOptions"
          :settings="{ packages: ['corechart'] }"
        />
      </div>
</template>

<script>
import {mapState, mapMutations} from 'vuex';
import { GChart } from 'vue-google-charts'

export default {
  name: 'chart',
  components: {
    GChart
  },
  data: function() {
    return {
      selectedChartType: "BarChart",
      chartTypes: [{value: "BarChart", text: "Bar Chart"},
                   {value: "PieChart", text: "Pie Chart"}],
      statusColors: {'claimed': '#ecdbff',
                     'completed': '#d4edda',
                     'expired': '#eef8b8',
                     'failed': '#f8d7da',
                     'pending': '#adadad',
                     'running': '#d1ecf1'},
    }
  },
  computed: {
    ...mapState({
        jobsGroupedByStatus: (state) => state.jobsGroupedByStatus,
    }),
    chartData: function() {
        let cd = [];
        cd.push(["Status", "Count", { role: 'style' }]);
        if (Object.keys(this.jobsGroupedByStatus).length) {
            // get counts per job status
            for (const [jobStatus, count] of 
                    Object.entries(this.jobsGroupedByStatus)) {
                let cd_entry = [];
                let label = jobStatus + " (" + count + ")";
                cd_entry = [label,
                            count,
                            'color: ' + this.statusColors[jobStatus]];
                cd.push(cd_entry);
            }
            return cd
        }
    },
    chartOptions: function() {
      if (this.selectedChartType == "PieChart") {
        return {
          pieHole: 0.4,
          chartArea: {left: '20%', width: '100%', height: '100%'},
          sliceVisibilityThreshold: 0,
          pieSliceTextStyle: {
            color: 'black',
            fontSize: 11
          },
          colors: Object.values(this.statusColors),
        }
      } else if (this.selectedChartType == "BarChart") {
        return {
          chartArea: {left: '35%', width: '30%', height: '100%'},
          legend: {position: 'none'},
        }
      }
    }
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

