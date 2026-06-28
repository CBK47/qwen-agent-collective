export class SkippyUI {
  constructor() {
    this.render();
  }

  render() {
    const container = document.createElement('div');
    container.className = 'skippy-ui-container';

    const header = document.createElement('h1');
    header.textContent = 'Skippy Concierge';
    container.appendChild(header);

    const seedSection = document.createElement('div');
    seedSection.className = 'seed-section';
    const seedTitle = document.createElement('h2');
    seedTitle.textContent = 'Seed New Device';
    seedSection.appendChild(seedTitle);

    const deviceIdInput = document.createElement('input');
    deviceIdInput.type = 'text';
    deviceIdInput.placeholder = 'Enter Device ID';
    deviceIdInput.id = 'device-id-input';
    seedSection.appendChild(deviceIdInput);

    const seedButton = document.createElement('button');
    seedButton.textContent = 'Seed Device';
    seedButton.id = 'seed-button';
    seedButton.addEventListener('click', () => {
      const deviceId = document.getElementById('device-id-input').value;
      this.seedDevice(deviceId);
    });
    seedSection.appendChild(seedButton);

    container.appendChild(seedSection);

    const deviceListSection = document.createElement('div');
    deviceListSection.className = 'device-list-section';
    const listTitle = document.createElement('h2');
    listTitle.textContent = 'Seeded Devices';
    deviceListSection.appendChild(listTitle);

    const deviceList = document.createElement('ul');
    deviceList.id = 'device-list';
    deviceListSection.appendChild(deviceList);

    container.appendChild(deviceListSection);

    const actionSection = document.createElement('div');
    actionSection.className = 'action-section';
    const actionTitle = document.createElement('h2');
    actionTitle.textContent = 'Execute Action';
    actionSection.appendChild(actionTitle);

    const actionSelect = document.createElement('select');
    actionSelect.id = 'action-select';
    const actions = ['Reboot', 'Update', 'Check Status'];
    actions.forEach(action => {
      const option = document.createElement('option');
      option.value = action.toLowerCase();
      option.textContent = action;
      actionSelect.appendChild(option);
    });
    actionSection.appendChild(actionSelect);

    const actionInput = document.createElement('input');
    actionInput.type = 'text';
    actionInput.placeholder = 'Action parameters';
    actionInput.id = 'action-params';
    actionSection.appendChild(actionInput);

    const executeButton = document.createElement('button');
    executeButton.textContent = 'Execute';
    executeButton.id = 'execute-button';
    executeButton.addEventListener('click', () => {
      const selectedAction = document.getElementById('action-select').value;
      const params = document.getElementById('action-params').value;
      this.executeAction(selectedAction, params);
    });
    actionSection.appendChild(executeButton);

    container.appendChild(actionSection);

    document.body.appendChild(container);
  }

  seedDevice(deviceId) {
    console.log(`Seeding device: ${deviceId}`);
    const deviceList = document.getElementById('device-list');
    const listItem = document.createElement('li');
    listItem.textContent = `Device ${deviceId} - Seeded`;
    deviceList.appendChild(listItem);
  }

  executeAction(action, params) {
    console.log(`Executing action: ${action} with params: ${params}`);
  }
}
