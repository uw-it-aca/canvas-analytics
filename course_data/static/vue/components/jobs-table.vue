<template>
  <div class="overflow-auto">
    <b-pagination
      v-model="currentPage"
      :total-rows="rows"
      :per-page="perPage"
      aria-controls="jobs-table"
      size="sm"
      limit="10"
      first-number
      last-number
      >
    </b-pagination>
    <b-table id="jobs-table"
      :items="filteredJobs"
      :fields="fields"
      :per-page="perPage"
      :busy="isLoading"
      :current-page="currentPage"
      fixed
      bordered
      small
      >
      <template #table-busy>
        <div class="text-center text-danger my-2">
          <b-spinner class="align-middle"></b-spinner>
          <strong>Loading...</strong>
        </div>
      </template>

      <template #cell(actions)="row">
        <b-button size="sm" @click="row.toggleDetails" class="mr-2">
          <b-icon icon="arrow-clockwise"></b-icon>
        </b-button>
      </template>
    </b-table>
  </div>
</template>

<script>
import {mapState, mapMutations} from 'vuex';

export default {
  name: 'jobs-table',
  data: function() {
    return {
      fields: [
        { key: 'course_code',
          label: 'Course',
          sortable: true,
        },
        { key: 'job_type',
          label: 'Job Type',
          sortable: true,
        },
        { key: 'start',
          label: 'Start',
          sortable: true,
        },
        { key: 'end',
          label: 'End',
          sortable: true,
        },
        { key: 'message',
          label: 'Status',
        },
        { key: 'actions',
          label: 'Actions'

        },
      ],
      perPage: 1000,
      currentPage: 1
    }
  },
  computed: {
    ...mapState({
      filteredJobs: (state) => state.filteredJobs,
      isLoading: (state) => state.isLoading,
      rows() {
        return this.filteredJobs.length
      }
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

