(() => {
  "use strict";

  const data = JSON.parse(document.getElementById("creation-data").textContent);
  const nameInput = document.getElementById("name");
  const departmentSelect = document.getElementById("department");
  const jobSelect = document.getElementById("job");
  const credits = document.getElementById("job-credits");
  const description = document.getElementById("job-description");
  const jobsByDepartment = Object.fromEntries(data.departments);

  function showJob(job) {
    const info = data.jobs[job];
    credits.textContent = info ? `${info.credits} cr` : "-";
    description.textContent = info ? info.description : "Select a department and job to see details.";
  }

  function rebuildJobs(selectedJob) {
    const jobs = jobsByDepartment[departmentSelect.value] || [];
    const options = jobs.length ? jobs : [data.selectJob];
    jobSelect.replaceChildren(...options.map((job) => new Option(job, job)));
    if (options.includes(selectedJob)) {
      jobSelect.value = selectedJob;
    }
    showJob(jobSelect.value);
  }

  document.getElementById("random-name").addEventListener("click", () => {
    nameInput.value = data.names[Math.floor(Math.random() * data.names.length)];
  });
  departmentSelect.addEventListener("change", () => rebuildJobs());
  jobSelect.addEventListener("change", () => showJob(jobSelect.value));

  rebuildJobs(jobSelect.dataset.selected);
})();
