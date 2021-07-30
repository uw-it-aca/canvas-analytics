<template>
  <div>
    <b-card-group deck>
      <b-card header-tag="header" footer-tag="footer">
        <template #header>
          <h6 class="mb-0">RAD Metadata Files</h6>
        </template>
        <b-form id="gcs_metadata_form">
          <b-form-group label="Term:" label-cols-sm="1" label-size="md">
            <b-form-select
              id="selected-term"
              v-model="selectedTerm"
              :options="terms"
            ></b-form-select>
          </b-form-group>
          <b-form-group label="Upload Type:" label-cols-sm="1" label-size="md">
            <b-form-select
              id="selected-upload-type"
              v-model="selectedUploadType"
              :options="uploadTypes"
            ></b-form-select>
          </b-form-group>
          <b-form-group label="Select File:" label-cols-sm="1" label-size="md">
            <b-form-file
              id="selected-file"
              v-model="selectedFile"
              placeholder="Choose a csv file or drop it here..."
              drop-placeholder="Drop csv file here..."
              accept=".csv"
            >
            </b-form-file>
          </b-form-group>
          <b-form-group label-cols-sm="1">
            <span>
              <b-button
                id="submit-gcs-metadata-form"
                :disabled="
                  !selectedTerm || !selectedUploadType || !selectedFile
                "
                variant="primary"
                @click="uploadFile()"
              >
                Upload
              </b-button>
              <label v-if="selectedTerm && selectedUploadType && selectedFile">
                Upload file name: {{ getNewFileName() }}
              </label>
            </span>
          </b-form-group>
        </b-form>
        <b-table-simple small caption-top responsive>
          <caption>
            Metadata files currently in the GCS bucket.
          </caption>
          <b-thead class="custom-thead">
            <b-tr>
              <b-th>Term</b-th>
              <b-th>EOP Advisers</b-th>
              <b-th>ISS Advisers</b-th>
              <b-th>Predicted Probabilites</b-th>
              <b-th>Student Categories</b-th>
            </b-tr>
          </b-thead>
          <b-tbody>
            <b-tr v-for="(item, term_id) in metadataFiles" :key="term_id">
              <b-th>{{ term_id }}</b-th>
              <b-td>
                <span v-if="item['eop-advisers']">
                  <b-icon @click="deleteUploadedFile(item['eop-advisers'].file_name)" icon="x-circle-fill" scale="1" class="delete-icon" variant="danger"></b-icon>
                  {{ item['eop-advisers'].file_name }}
                </span>
                <span v-else class="text-secondary">N/A</span>
              </b-td>
              <b-td>
                <span v-if="item['iss-advisers']">
                  <b-icon @click="deleteUploadedFile(item['iss-advisers'].file_name)" icon="x-circle-fill" scale="1" class="delete-icon" variant="danger"></b-icon>
                  {{ item['iss-advisers'].file_name }}
                </span>
                <span v-else class="text-secondary">N/A</span>
              </b-td>
              <b-td>
                <span v-if="item['pred-proba']">
                  <b-icon @click="deleteUploadedFile(item['pred-proba'].file_name)" icon="x-circle-fill" scale="1" class="delete-icon" variant="danger"></b-icon>
                  {{ item['pred-proba'].file_name }}
                </span>
                <span v-else class="text-secondary">N/A</span>
              </b-td>
              <b-td>
                <span v-if="item['netid-name-stunum-categories']">
                  <b-icon @click="deleteUploadedFile(item['netid-name-stunum-categories'].file_name)" icon="x-circle-fill" scale="1" class="delete-icon" variant="danger"></b-icon>
                  {{ item['netid-name-stunum-categories'].file_name }}
                </span>
                <span v-else class="text-secondary">N/A</span>
              </b-td>
            </b-tr>
          </b-tbody>
        </b-table-simple>
      </b-card>
    </b-card-group>
  </div>
</template>

<script>
import { mapState, mapMutations } from "vuex";
import dataMixin from "../../mixins/data_mixin";

export default {
  name: "admin-metadata",
  mixins: [dataMixin],
  created: function () {
    this.selectedTerm = this.terms[0];
    this.selectedUploadType = this.uploadTypes[0].value;
  },
  data: function () {
    return {
      selectedFile: null,
      selectedTerm: null,
      selectedUploadType: null,
      newFileName: null,
      uploadTypes: [
        { text: "EOP Advisers", value: "eop-advisers" },
        { text: "ISS Advisers", value: "iss-advisers" },
        { text: "Predicted Probabilites", value: "pred-proba" },
        { text: "Student Categories", value: "netid-name-stunum-categories" },
      ],
    };
  },
  computed: {
    ...mapState({
      gcsMetadataForm: (state) => state.gcsMetadataForm,
      metadataFiles: (state) => state.metadataFiles,
      terms: (state) => state.terms,
    }),
  },
  methods: {
    ...mapMutations([]),
    getNewFileName: function () {
      return this.selectedTerm + "-" + this.selectedUploadType + ".csv";
    },
    showFileInfoMessage: function(message, fileName) {
      const h = this.$createElement;
      const warningVNode = h('div', [
        h('p', {class: ['text-left']}, [
          message + ":",
          h('br'),
          h('b', fileName),
        ]),
      ]);
      return this.$bvModal.msgBoxOk(
        warningVNode,
        {
          title: 'Notice',
          size: 'md',
          buttonSize: 'md',
          okVariant: 'secondary',
          okTitle: 'Dismiss',
          footerClass: 'p-2',
          hideHeaderClose: false,
          centered: true
      })

    },
    showConfirmFileActionWarning: function(action, fileName) {
      // create warning message
      const h = this.$createElement;
      const warningVNode = h('div', [
        h('p', {class: ['text-left']}, [
          'Please confirm that you want to ',
          h('b', action),
          ' the following file:',
          h('br'),
          h('b', fileName),
        ]),
      ]);

      return this.$bvModal.msgBoxConfirm(
        warningVNode,
        {
          title: 'Please Confirm',
          size: 'md',
          buttonSize: 'md',
          okVariant: 'primary',
          okTitle: 'Yes',
          cancelVariant: 'secondary',
          cancelTitle: 'No',
          footerClass: 'p-2',
          hideHeaderClose: false,
          centered: true
      })
    },
    uploadFile: function () {
      let formData = new FormData();
      formData.append(
        "upload",
        document.getElementById("selected-file").files[0]
      );
      let newFileName = this.getNewFileName()
      formData.append("newFileName", newFileName);
      formData.append("uploadType", this.selectedUploadType);
      formData.append("term", this.selectedTerm);

      // show dialog if a file already exists
      let existing_file = this.metadataFiles[this.selectedTerm][this.selectedUploadType];
      if (existing_file) {
        this.showFileInfoMessage("The following file already exists", newFileName);
        return;
      }

      var _this = this;
      this.showConfirmFileActionWarning("upload", newFileName).then(choice => {
        if (choice) {
          _this.uploadMetadataFile(formData).then(() => {
            _this.$parent.refreshMetadata();
            _this.showFileInfoMessage("Upload successful", newFileName)
          });
        }
      });
    },
    deleteUploadedFile: function (fileName) {
      var _this = this;
      this.showConfirmFileActionWarning("delete", fileName).then(choice => {
        if (choice) {
          _this.deleteMetadataFile(fileName).then(() => {
            _this.$parent.refreshMetadata();
            _this.showFileInfoMessage("Delete successful", fileName)
          });
        }
      });
    }
  },
};
</script>

<style>
#gcs_metadata_form {
  margin-bottom: 25px;
}
</style>
