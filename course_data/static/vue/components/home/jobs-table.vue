<template>
  <div class="overflow-auto">
    <b-pagination
      v-model="currentPage"
      :total-rows="totalRows"
      :per-page="perPage"
      aria-controls="jobs-table"
      size="sm"
      limit="10"
      first-number
      last-number
      >
    </b-pagination>
    <b-table id="jobs-table"
      :items="jobs"
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
        <b-button v-show="getStatus(row.item) == 'error' || getStatus(row.item) == 'complete'" size="sm" @click="restartJobs([row.item.id])" class="mr-2">
          <b-icon icon="arrow-clockwise"></b-icon>
        </b-button>
        <b-button size="sm" @click="setPending(row)" class="mr-2">
          set pending
        </b-button>
        <b-button size="sm" @click="setRunning(row)" class="mr-2">
          set running
        </b-button>
        <b-button size="sm" @click="setComplete(row)" class="mr-2">
          set complete
        </b-button>
        <b-button size="sm" @click="setError(row)" class="mr-2">
          set error
        </b-button>
      </template>
    </b-table>
  </div>
</template>

<script>
import {mapState, mapMutations} from 'vuex';
import dataMixin from '../../mixins/data_mixin';

export default {
  name: 'jobs-table',
  mixins: [dataMixin],
  props: ['jobs'],
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
          tdClass: (value, key, item) => {
              return 'table-' + this.getStatus(item);
          },
          formatter: 'statusFormatter'
        },
        { key: 'actions',
          label: 'Actions'
        },
      ],
      perPage: 500,
      currentPage: 1
    }
  },
  computed: {
    ...mapState({
      isLoading: (state) => state.isLoading,
      totalRows() {
        return this.jobs.length
      }
    }),
  },
  methods: {
    setPending: function(row) {
      row.item.pid = "";
      row.item.start = ""
      row.item.end = ""
      row.item.message = ""
    },
    setRunning: function(row) {
      row.item.pid = "1234";
      row.item.start = "2021-01-01"
      row.item.end = ""
      row.item.message = ""
    },
    setComplete: function(row) {
      row.item.pid = "1234";
      row.item.start = "2021-01-01"
      row.item.end = "2021-01-01"
      row.item.message = ""
    },
    setError: function(row) {
      row.item.pid = "1234";
      row.item.start = "2021-01-01"
      row.item.end = ""
      row.item.message = "MOCK ERROR OCCURED"
    },
    getStatus: function(item) {
      if (!item.pid && !item.start && !item.end && !item.message)
        return "pending";
      else if (item.pid && item.start && !item.end && !item.message)
        return "running";
      else if (item.pid && item.start && item.end && !item.message)
        return "complete";
      else if (item.message)
        return "error";
    },
    statusFormatter: function(value, key, item) {
      return this.getStatus(item);
    },
    ...mapMutations([
      'addVarToState',
    ]),
  },
};
</script>

<style>
  .table-pending {
    color: #818182;
    background-color: #fefefe;
    border-color: #fdfdfe;
  }

  .table-running {
    color: #0c5460;
    background-color: #d1ecf1;
    border-color: #bee5eb;
  }

  .table-complete {
    color: #155724;
    background-color: #d4edda;
    border-color: #c3e6cb;
  }

  .table-error {
    color: #721c24;
    background-color: #f8d7da;
    border-color: #f5c6cb;
  }
</style>

