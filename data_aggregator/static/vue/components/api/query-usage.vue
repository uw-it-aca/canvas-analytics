<template>
<p>
  <b-card bg-variant="light"  class="mt-2 mb-2">
    <b-card-text>
<pre>
/api/v1/account/(resource-id)/analytics/(analytics-type)/? [sis_term_id=&ltstring&gt] [week=&ltinteger&gt]
or
/api/v1/term/(resource-id)/analytics/(analytics-type)/? [week=&ltinteger&gt]
or
/api/v1/user/(resource-id)/analytics/(analytics-type)/? [sis_term_id=&ltstring&gt] [week=&ltinteger&gt]
or
/api/v1/user/? [has_analytics=&ltboolean&gt]
</pre>
    </b-card-text>
  </b-card>
  where
  <b-card bg-variant="light"  class="mt-2 mb-2">
    <b-card-text>
<pre>
(resource-id)
      /api/v1/account/   ::    (sis-account-id)
      /api/v1/term/      ::    (sis-term-id)
      /api/v1/user/      ::    (sis-user-id)
(analytics-type)         ::    ("assignment") or ("participation")
</pre>
    </b-card-text>
  </b-card>
  (..) required<br/>
  [..] optional<br/>
</p>
</template>

<script>
import {mapState, mapMutations} from 'vuex';

export default {
  name: 'api-usage',
  computed: {
    ...mapState({
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

