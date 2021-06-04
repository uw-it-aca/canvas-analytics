<template>
    <span>
      ({{executionTime}})
    </span>
</template>

<script>
import {mapState, mapMutations} from 'vuex';
import utilities from "../../../../js/utilities.js";
import moment from 'moment';

export default {
  name: 'time-difference-widget',
  props: ['startTime'],
  created: function() {
    setInterval(this.refreshExecutionTime, 1000);
  },
  data: function() {
    return {
        executionTime: 0,
    }
  },
  methods: {
    ...mapMutations([
      'addVarToState',
    ]),
    refreshExecutionTime: function() {
      let start = moment.utc(this.startTime);
      let now = moment.utc();
      let duration = moment.duration(now.diff(start));
      this.executionTime = utilities.formatDuration(duration);
    }
  },
};
</script>

<style lang="scss" scoped>
</style>

