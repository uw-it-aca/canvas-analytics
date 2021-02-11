<template>
  <b-table-simple small responsive bordered class="mt-4">
    <b-thead>
      <b-tr>
        <b-th>parameter</b-th>
        <b-th>example</b-th>
        <b-th>description</b-th>
        <b-th>default</b-th>
        <b-th>type</b-th>
      </b-tr>
    </b-thead>
    <b-tbody>
      <b-tr v-for="param in queryparams" :key="param.name">
        <b-td>{{param.name}}</b-td>
        <b-td>{{param.example}}</b-td>
        <b-td>{{param.description}}</b-td>
        <b-td><i>{{param.default}}</i></b-td>
        <b-td>{{param.type}}</b-td>
      </b-tr>
      <b-tr>
        <b-td colspan="5"><b>/api/v1/account/ endpoint</b></b-td>
      </b-tr>
      <b-tr v-for="param in accountparams" :key="param.name">
        <b-td>{{param.name}}</b-td>
        <b-td>{{param.example}}</b-td>
        <b-td>{{param.description}}</b-td>
        <b-td><i>{{param.default}}</i></b-td>
        <b-td>{{param.type}}</b-td>
      </b-tr>
      <b-tr>
        <b-td colspan="5"><b>/api/v1/term/ endpoint</b></b-td>
      </b-tr>
      <b-tr v-for="param in termparams" :key="param.name">
        <b-td>{{param.name}}</b-td>
        <b-td>{{param.example}}</b-td>
        <b-td>{{param.description}}</b-td>
        <b-td><i>{{param.default}}</i></b-td>
        <b-td>{{param.type}}</b-td>
      </b-tr>
      <b-tr>
        <b-td colspan="5"><b>/api/v1/student/ endpoint</b></b-td>
      </b-tr>
      <b-tr v-for="param in studentparams" :key="param.name">
        <b-td>{{param.name}}</b-td>
        <b-td>{{param.example}}</b-td>
        <b-td>{{param.description}}</b-td>
        <b-td><i>{{param.default}}</i></b-td>
        <b-td>{{param.type}}</b-td>
      </b-tr>
    </b-tbody>
  </b-table-simple>
</template>

<script>
import {mapState, mapMutations} from 'vuex';

export default {
  name: 'api-query-param-description',
  data: function() {
    return {
      queryparams: [
        {name: "week",
         example: "5",
         description: "Week in a term",
         default: "any",
         type: "int"},
        {name: "sis_term_id",
         example: "Spring-2021",
         description: "Term id in format [Year]-[Quarter]",
         default: "any",
         type: "string"}
      ],
      accountparams: [
        {name: "sis-account-id",
         example: "uwcourse:seattle:arts-sciences:engineering:CSE",
         description: "Sub account id identifying the scope of control",
         default: "required",
         type: "string"},
      ],
      termparams: [
        {name: "sis-term-id",
         example: "Spring-2021",
         description: "Term id in format [Year]-[Quarter]",
         default: "required",
         type: "string"}
      ],
      studentparams: [
        {name: "canvas-student-id",
         example: "3715220",
         description: "Internal canvas student id",
         default: "required",
         type: "int"},
      ],
    }
  },
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

