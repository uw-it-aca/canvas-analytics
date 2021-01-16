<template>
  <b-container fluid>
    <b-row align-h="between">
      <b-col xs="12" md="6">
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
      </b-col>
      <b-col xs="12" md="6">
        <b-form class="d-flex flex-nowrap" inline>
          <label class="mr-2">Action</label>
          <b-form-select v-model="selectedAction" id="action-select" name="action-select">
            <b-form-select-option :value="'restart'">restart selected</b-form-select-option>
          </b-form-select>
          <b-button @click="handleAction()" variant="primary" size="md" class="mr-2">
            Run
          </b-button>
        </b-form>
      </b-col>
    </b-row>
    <b-row>
      <b-col xs="12">
        <b-table id="jobs-table"
          :items="jobs"
          :fields="fields"
          :per-page="perPage"
          :busy="isLoading"
          :current-page="currentPage"
          :primary-key="'id'"
          stacked="sm"
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

          <template #table-colgroup="scope">
            <col
              v-for="field in scope.fields"
              :key="field.key"
              :style="{ width: _getColumnWidth(field.key) }"
            >
          </template>

          <template slot="thead-top" slot-scope="{ fields }">
            <td v-for="field in fields" :key="field.key">
              <b-form-select v-if="field.key == 'message'" class="small-select" id="jobstatuses" name="jobstatus" v-model="filters.job_status">
                <b-form-select-option :value="'all'" selected>all</b-form-select-option>
                <b-form-select-option :value="'pending'">pending</b-form-select-option>
                <b-form-select-option :value="'running'">running</b-form-select-option>
                <b-form-select-option :value="'completed'">completed</b-form-select-option>
                <b-form-select-option :value="'failed'">failed</b-form-select-option>
              </b-form-select>

              <b-form-select v-if="field.key == 'job_type'" class="small-select" id="jobtypes" name="jobtype"  v-model="filters.job_type">
                <b-form-select-option :value="'all'" selected>all</b-form-select-option>
                <b-form-select-option v-for="jobtype in jobtypes" :key="jobtype.id" :value="jobtype.type">{{jobtype.type}}</b-form-select-option>
              </b-form-select>
            </td>
          </template>

          <template #head(selected)="">
            <input type="checkbox" id="checkbox" @click="selectAll" v-model="allSelected">
          </template>

          <template #cell(selected)="row">
            <input type="checkbox" id="checkbox" @click="select" v-model="row.item.selected">
          </template>

          <template #cell(context)="row">
            <ul class="list-unstyled m-0">
              <li v-for="(value, name) in row.item.context" :key="value">
                {{name}} : {{ value }}
              </li>
            </ul>
          </template>

          <template #cell(start)="row">
            {{row.item.start | date}}
          </template>

          <template #cell(end)="row">
            {{row.item.end | date}}
          </template>
      
          <template #cell(message)="row">
            {{getStatus(row.item)}}
          </template>
        </b-table>
      </b-col>
    </b-row>
  </b-container>
</template>

<script>
import {mapState, mapMutations} from 'vuex';
import dataMixin from '../../mixins/data_mixin';
import utilitiesMixin from '../../mixins/utilities_mixin';

export default {
  name: 'jobs-table',
  mixins: [dataMixin, utilitiesMixin],
  props: ['jobs', 'selectedJobs'],
  created: function() {
    // default to all job types
    this.$store.commit('setJobType', "all");
    // default to all job statuses
    this.$store.commit('setJobStatus', "all");
  },
  data: function() {
    return {
      fields: [
        { key: 'selected',
          label: '',
          sortable: false,
        },
        { key: 'job_type',
          label: 'Job Type',
          sortable: true,
        },
        { key: 'context',
          label: 'Job Context',
          sortable: true,
        },
        { key: 'message',
          label: 'Job Status',
          tdClass: (value, key, item) => {
              return 'table-' + this.getStatus(item);
          },
        },
        { key: 'start',
          label: 'Job Start',
          sortable: true,
        },
        { key: 'end',
          label: 'Job End',
          sortable: true,
        },
      ],
      perPage: 250,
      currentPage: 1,
      selectedAction: 'restart',
      allSelected: false,
    }
  },
  computed: {
    ...mapState({
      filters: (state) => state.filters,
      jobtypes: (state) => state.jobtypes,
      isLoading: (state) => state.isLoading,
      totalRows() {
        return this.jobs.length
      }
    }),
  },
  methods: {
    handleAction: function() {
      if (this.selectedAction == 'restart') {
        let _this = this;
        let jobsToRestart = this.selectedJobs.filter(
          job => (this.getStatus(job) == "completed" ||  this.getStatus(job) == "failed"));
        this.restartJobs(jobsToRestart).then(function() {
          jobsToRestart.forEach(function (job, index) {
            _this._setLocalPendingStatus(job);
          });
        });
      }
    },
    selectAll: function() {
      let _this = this;
      this.jobs.forEach(function (job, index) {
        job.selected = !_this.allSelected;
      });
    },
    select: function() {
      this.allSelected = false;
    },
    _getColumnWidth: function(field_key) {
      if(field_key == "message")
        return "120%";
      else if (field_key == "selected")
        return "25px";
      else
        return "100%";
    },
    _setLocalPendingStatus: function(job) {
      job.pid = "";
      job.start = ""
      job.end = ""
      job.message = ""
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

  .table-completed {
    color: #155724;
    background-color: #d4edda;
    border-color: #c3e6cb;
  }

  .table-failed {
    color: #721c24;
    background-color: #f8d7da;
    border-color: #f5c6cb;
  }

  .small-select {
    height: 25px;
    padding: 0px 5px;
    width: 100% !important;
  }

  .pill-button {
    background-color: #ddd;
    border-style: solid;
    border-width: 1px;
    border-radius: 4px;
    border-color: darkgray;
    color: black;
    padding: 3px 5px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    margin: 2px 1px;
    cursor: pointer;
    font-size: 10px;
  }
</style>

