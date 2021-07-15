<template>
  <dl>
    <dt>Type</dt>
    <dd v-if="job.type">{{job.type}}</dd>
    <dd v-else>N/A</dd>

    <dt>Status</dt>
    <dd v-if="job.status">
      <b-badge :class="job.status">{{job.status}}</b-badge>
    </dd>
    <dd v-else>N/A</dd>

    <dt>Start</dt>
    <dd v-if="job.start">{{job.start}}</dd>
    <dd v-else>N/A</dd>

    <dt>End</dt>
    <dd v-if="job.end">{{job.end}}</dd>
    <dd v-else>N/A</dd>

    <dt>Execution Time</dt>
    <dd v-if="job.start && job.end">{{job | execution_time}}</dd>
    <dd v-else>N/A</dd>

    <dt>Active Range Start</dt>
    <dd v-if="job.target_date_start">{{job.target_date_start}}</dd>
    <dd v-else>N/A</dd>

    <dt>Active Range End</dt>
    <dd v-if="job.target_date_end">{{job.target_date_end}}</dd>
    <dd v-else>N/A</dd>

    <dt>Context</dt>
    <dd v-if="job.context"><pre>{{job.context}}</pre></dd>
    <dd v-else>N/A</dd>

    <dt>Error</dt>
    <dd v-if="job.message"><pre>{{job.message}}</pre></dd>
    <dd v-else>N/A</dd>

    <dt>Created</dt>
    <dd v-if="job.created">{{job.created}}</dd>
    <dd v-else>N/A</dd>
  </dl>
</template>

<script>
import {mapState, mapMutations} from 'vuex';
import utilitiesMixin from '../../mixins/utilities_mixin';

export default {
  name: 'api-query-param-description',
  mixins: [utilitiesMixin],
  computed: {
    ...mapState({
        job: (state) => state.job,
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
