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
        {desciption: "All participation records for UW Seattle canvas for Summer 2012 term Week 2",
         name: origin + "/api/v1/account/uwcourse:seattle/participation/?sis_term_id=2021-summer&week=2",
         href: origin + "/api/v1/account/uwcourse:seattle/participation/?sis_term_id=2021-summer&week=2"},
        {desciption: "All assignment records for Summer 2021 term",
         name: origin + "/api/v1/term/2021-summer/assignment/",
         href: origin + "/api/v1/term/2021-summer/assignment/"},
        {desciption: "All participation records for Summer 2021 term Week 2",
         name: origin + "/api/v1/term/2021-summer/participation/?week=2",
         href: origin + "/api/v1/term/2021-summer/participation/?week=2"},
        {desciption: "All users in the canvas analytics db with analytics",
         name: origin + "/api/v1/user/?has_anaytics=true",
         href: origin + "/api/v1/user/?has_anaytics=true"},
        {desciption: "All users in the canvas analytics db without analytics",
         name: origin + "/api/v1/user/?has_anaytics=false",
         href: origin + "/api/v1/user/?has_anaytics=false"},
        {desciption: "All assignment records from Summer 2021 term, Week 2 for user with sis user id ABF403FC8E3541ADBACFB411F3CBA075",
         name: origin + "/api/v1/user/ABF403FC8E3541ADBACFB411F3CBA075/assignment/?sis_term_id=2021-summer&week=2",
         href: origin + "/api/v1/user/ABF403FC8E3541ADBACFB411F3CBA075/assignment/?sis_term_id=2021-summer&week=2"},
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
