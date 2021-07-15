<template>
    <div class="top-right-corner">
      <b-badge variant="secondary">
        Current Time: {{currentTime | iso_date}}
      </b-badge>
    </div>
</template>

<script>
import {mapState, mapMutations} from 'vuex';
import utilitiesMixin from '../../../mixins/utilities_mixin';
import moment from 'moment';

export default {
  name: 'timewidget',
  mixins: [utilitiesMixin],
  created: function() {
    setInterval(this.refreshCurrentTime, 1000);
  },
  data: function() {
    return {
        currentTime: moment()
    }
  },
  methods: {
    ...mapMutations([
      'addVarToState',
    ]),
    refreshCurrentTime: function() {
        this.currentTime = moment();
    }
  },
};
</script>

<style lang="scss" scoped>
    .top-right-corner {
      position: absolute;
      top: 0px;
      right: 30px;
    }
</style>

