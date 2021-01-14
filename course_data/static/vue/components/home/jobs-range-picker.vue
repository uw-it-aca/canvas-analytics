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

export default {
  name: 'jobs-range-picker',
  mixins: [dataMixin],
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
      }
    }
  },
  filters: {
    date(val) {
      var options = {
          year: "numeric",
          month: "2-digit",
          day: "numeric"
      };
      return val ? val.toLocaleString('en-US', options) : '';
    }
  },
  computed: {
    ...mapState({
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
    // default to first pre-set range
    if (this.dateRanges) {
      let key = Object.keys(this.dateRanges)[0];
      let default_range = {
        startDate: this.dateRanges[key][0],
        endDate: this.dateRanges[key][1]
      };
      this.selected_date_range = default_range;
    }
  },
  methods: {
    ...mapMutations([
      'setSelectedDateRange',
    ]),
  },
};
</script>

<style scoped>
  .ranges-ul {
    height: 250px;
    overflow-y: scroll;
  }
</style>

