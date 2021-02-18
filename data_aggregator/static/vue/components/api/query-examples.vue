<template>
  <ul>
    <li v-for="link in links" :key="link.href">{{link.desciption}}<br/>
      <a :href="link.href">{{link.name}}</a>
    </li>
  </ul>
</template>

<script>
import {mapState, mapMutations} from 'vuex';

export default {
  name: 'api-query-examples',

  computed: {
    links: function() {
      let origin = window.location.origin;
      return [
        {desciption: "All participation records for UW Seattle canvas for Winter 2012 term Week 5",
         name: origin + "/api/v1/account/uwcourse:seattle/participation/?sis_term_id=2021-winter&week=5",
         href: origin + "/api/v1/account/uwcourse:seattle/participation/?sis_term_id=2021-winter&week=5"},
        {desciption: "All assignment records for Winter 2021 term",
         name: origin + "/api/v1/term/2021-winter/assignment/",
         href: origin + "/api/v1/term/2021-winter/assignment/"},
        {desciption: "All participation records for Winter 2021 term Week 5",
         name: origin + "/api/v1/term/2021-winter/participation/?week=5",
         href: origin + "/api/v1/term/2021-winter/participation/?week=5"},
        {desciption: "All users in the canvas analytics db with analytics",
         name: origin + "/api/v1/user/?has_anaytics=true",
         href: origin + "/api/v1/user/?has_anaytics=true"},
        {desciption: "All users in the canvas analytics db without analytics",
         name: origin + "/api/v1/user/?has_anaytics=false",
         href: origin + "/api/v1/user/?has_anaytics=false"},
        {desciption: "All assignment records from Winter 2021 term, Week 5 for user with sis user id 4DC8FAF817814361889CB2715CD16D28",
         name: origin + "/api/v1/user/4DC8FAF817814361889CB2715CD16D28/assignment/?sis_term_id=2021-winter&week=5",
         href: origin + "/api/v1/user/4DC8FAF817814361889CB2715CD16D28/assignment/?sis_term_id=2021-winter&week=5"},
      ];
    },
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

