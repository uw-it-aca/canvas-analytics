<template>
  <date-range-picker
    ref="picker"
    :opens="'right'"
    :locale-data="dateLocale"
    :singleDatePicker="false"
    :showDropdowns="true"
    :timePicker="true"
    :timePicker24Hour="true"
    :showWeekNumbers="true"
    :autoApply="true"
    :ranges="dateRanges"
    :date-format="dateFormat"
    v-model="activeDateRange"
    class="mr-2"
  >
    <template v-slot:input="picker" style="min-width: 350px;">
        {{ picker.startDate | iso_date }} - {{ picker.endDate | iso_date}}
    </template>

    <template #ranges="ranges">
      <div class="ranges">
        <ul class="ranges-ul">
          <li v-for="(range, name) in ranges.ranges" :key="name" @click="ranges.clickRange(range)">
            <b>{{name}}</b><br/>
            <small class="text-muted">{{range[0] | short_date}} - {{range[1] | short_date }}</small>
          </li>
        </ul>
      </div>
    </template>

  </date-range-picker>
</template>

<script>
import {mapState, mapMutations} from 'vuex';
import moment from 'moment';
import dataMixin from '../../mixins/data_mixin';
import utilitiesMixin from '../../mixins/utilities_mixin';
import datePickerMixin from '../../mixins/datepicker_mixin';

export default {
  name: 'active-range-picker',
  mixins: [dataMixin, utilitiesMixin, datePickerMixin],
  computed: {
    ...mapState({
      jobRanges: (state) => state.jobRanges,
      terms: (state) => state.terms,
    }),
    activeDateRange: {
      get () {
        return this.$store.state.activeDateRange;
      },
      set (value) {
        this.$store.commit('setActiveDateRange', value);
      }
    },
    dateRanges: function() {
      let ranges = {};
      this.terms.forEach(function (term, index) {
        ranges["Today"] = [moment.utc().startOf('day').toDate(), moment.utc().endOf('day').toDate()];
        var rangeLabel = term.quarter.charAt(0).toUpperCase() + term.quarter.slice(1) + ", " + term.year;
        ranges[rangeLabel] = [moment.utc(term.first_day_quarter).toDate(), moment.utc(term.grade_submission_deadline).toDate()];
      });
      return ranges;
    },
  },
  methods: {
    dateFormat (classes, date) {
      classes['contains-jobs'] = this.doesDateHaveActiveJobs(date);
      return classes;
    },
    doesDateHaveActiveJobs: function(date) {
      for (var idx in this.jobRanges) {
        var jobRange = this.jobRanges[idx];
        var calDay = moment(date).utc().format("YYYY-MM-DD");
        var targetStartDay = moment(jobRange.target_day_start).utc().format("YYYY-MM-DD");
        var targetEndDay = moment(jobRange.target_day_end).utc().format("YYYY-MM-DD");
        if (calDay >= targetStartDay && calDay <= targetEndDay) {
          return true;
        }
      }
      return false;
    },
    ...mapMutations([
      'setActiveDateRange',
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

