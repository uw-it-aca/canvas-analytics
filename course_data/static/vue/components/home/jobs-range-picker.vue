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
          v-model="selected_date_range"
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

export default {
  name: 'jobs-range-picker',
  mixins: [dataMixin, utilitiesMixin],
  data: function() {
    return {
      dateLocale: {
        direction: 'ltr',
        format: 'mm/dd/yyyy',
        separator: ' - ',
        applyLabel: 'Apply',
        cancelLabel: 'Cancel',
        weekLabel: 'W',
        customRangeLabel: 'Custom Range',
        daysOfWeek: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
        monthNames: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        firstDay: 0
      },
    }
  },
  computed: {
    ...mapState({
      job_ranges: (state) => state.job_ranges,
      terms: (state) => state.terms,
    }),
    selected_date_range: {
      get () {
        return this.$store.state.selected_date_range;
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
    let today = new Date();
    let firstDayMonth = new Date(today.getFullYear(), today.getMonth(), 1);
    let lastDayMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0);
    let default_range = {
      startDate: firstDayMonth,
      endDate: lastDayMonth
    };
    this.selected_date_range = default_range;
  },
  methods: {
    dateFormat (classes, date) {
      classes['contains-jobs'] = this.doesDateHaveJobs(date);
      return classes;
      
    },
    doesDateHaveJobs: function(date) {
      console.log(this.job_ranges);
      for (var idx in this.job_ranges) {
        var job_range = this.job_ranges[idx];
        var calDay = new Date(new Date(date).getFullYear(),
                              new Date(date).getMonth(),
                              new Date(date).getDate());
        var targetStartDay = new Date(new Date(job_range.target_day_start).getFullYear(),
                                      new Date(job_range.target_day_start).getMonth(),
                                      new Date(job_range.target_day_start).getDate());
        var targetEndDay = new Date(new Date(job_range.target_day_end).getFullYear(),
                                    new Date(job_range.target_day_end).getMonth(),
                                    new Date(job_range.target_day_end).getDate());
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

