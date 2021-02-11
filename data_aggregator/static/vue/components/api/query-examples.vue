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
        {desciption: "All assignment records from Winter 2021 term, Week 5 for student with canvas id 3715220",
         name: origin + "/api/v1/student/3715220/assignment/?sis_term_id=2021-winter&week=4",
         href: origin + "/api/v1/student/3715220/assignment/?sis_term_id=2021-winter&week=4"},
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

