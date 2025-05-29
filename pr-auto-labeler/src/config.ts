const fileLabelMappings = [
  {
    pattern: '.md',
    label: 'documentation'
  },
  {
    pattern: 'README',
    label: 'documentation'
  },
  {
    pattern: 'CONTRIBUTING',
    label: 'documentation'
  },
  {
    pattern: 'algorithm',
    label: 'Algorithm'
  },
  {
    pattern: 'pr_analysis',
    label: 'Algorithm'
  },
  {
    pattern: '.github/workflows',
    label: 'enhancement'
  },
  {
    pattern: 'test',
    label: 'bug'
  },
  {
    pattern: 'fix',
    label: 'bug'
  },
  {
    pattern: 'refactor',
    label: 'refactoring'
  }
];

export default fileLabelMappings;
export { fileLabelMappings };
