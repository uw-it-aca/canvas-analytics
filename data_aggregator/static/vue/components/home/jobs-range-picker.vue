<template>
  <date-range-picker
          ref="picker"
          :opens="'right'"
          :locale-data="dateLocale"
          :singleDatePicker="false"
          :showDropdowns="true"
          :timePicker="false"
          :showWeekNumbers="true"
          :autoApply="true"
          :ranges="dateRanges"
          :date-format="dateFormat"
          v-model="selectedDateRange"
          class="mr-2"
  >
    <template v-slot:input="picker" style="min-width: 350px;">
        {{ picker.startDate | date }} - {{ picker.endDate | date}}
    </template>

    <template #ranges="ranges">
      <div class="ranges">
        <ul class="ranges-ul">
          <li v-for="(range, name) in ranges.ranges" :key="name" @click="ranges.clickRange(range)">
            <b>{{name}}</b><br/>
            <small class="text-muted">{{range[0] | date}} - {{range[1] | date }}</small>
          </li>
        </ul>
      </div>
    </template>

  </date-range-picker>
</template>

<script>
import {mapState, mapMutations} from 'vuex';
import dataMixin from '../../mixins/data_mixin';
import utilitiesMixin from '../../mixins/utilities_mixin';
import datePickerMixin from '../../mixins/datepicker_mixin';

export default {
  name: 'jobs-range-picker',
  mixins: [dataMixin, utilitiesMixin, datePickerMixin],
  computed: {
    ...mapState({
      jobRanges: (state) => state.jobRanges,
      terms: (state) => state.terms,
    }),
    selectedDateRange: {
      get () {
        return this.$store.state.selectedDateRange;
      },
      set (value) {
        this.$store.commit('setSelectedDateRange', value);
      }
    },
    dateRanges: function() {
      let ranges = {};
      this.terms.forEach(function (term, index) {
        var rangeLabel = term.quarter.charAt(0).toUpperCase() + term.quarter.slice(1) + ", " + term.year;
        ranges[rangeLabel] = [new Date(term.first_day_quarter), new Date(term.grade_submission_deadline)];
      });
      return ranges;
    },
  },
  created: function() {
    // default to current month
    if (!this.selectedDateRange.startDate && !this.selectedDateRange.endDate) {
      let today = new Date();
      let firstDayMonth = new Date(today.getFullYear(), today.getMonth(), 1);
      let lastDayMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0);
      let defaultRange = {
        startDate: firstDayMonth,
        endDate: lastDayMonth
      };
      this.selectedDateRange = defaultRange;
    }
  },
  methods: {
    dateFormat (classes, date) {
      classes['contains-jobs'] = this.doesDateHaveJobs(date);
      return classes;
    },
    doesDateHaveJobs: function(date) {
      for (var idx in this.jobRanges) {
        var jobRange = this.jobRanges[idx];
        var calDay = new Date(new Date(date).getFullYear(),
                              new Date(date).getMonth(),
                              new Date(date).getDate());
        var targetStartDay = new Date(new Date(jobRange.target_day_start).getFullYear(),
                                      new Date(jobRange.target_day_start).getMonth(),
                                      new Date(jobRange.target_day_start).getDate());
        var targetEndDay = new Date(new Date(jobRange.target_day_end).getFullYear(),
                                    new Date(jobRange.target_day_end).getMonth(),
                                    new Date(jobRange.target_day_end).getDate());
        if (calDay >= targetStartDay && calDay <= targetEndDay) {
          return true;
        }
      }
      return false;
    },
    ...mapMutations([
      'setSelectedDateRange',
    ]),
  },
};
</script>

<style>
  .ranges-ul {
    height: 250px;
    overflow-y: scroll;
  }
  .contains-jobs {
    background-color: lightgreen !important;
  }
</style>

