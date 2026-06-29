export class SkippyUI {
  constructor() {
    this.render();
  }

  render() {
    const style = document.createElement('style');
    style.textContent = `
      .skippy-ui-container {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
        background: #ffffff;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
      }
      .header {
        display: flex;
        align-items: center;
        margin-bottom: 20px;
      }
      .header img {
        width: 40px;
        height: 40px;
        margin-right: 10px;
      }
      h1 {
        color: #007bff;
        margin: 0;
        font-size: 24px;
      }
      .seed-section, .device-list-section, .action-section {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 6px;
        margin-bottom: 20px;
      }
      h2 {
        color: #333;
        margin-top: 0;
        margin-bottom: 10px;
        font-size: 18px;
      }
      button {
        background: #007bff;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        cursor: pointer;
        transition: background 0.3s;
      }
      button:hover {
        background: #0056b3;
      }
      input {
        padding: 8px;
        border: 1px solid #ddd;
        border-radius: 4px;
        width: 100%;
        margin-bottom: 10px;
      }
      ul {
        list-style-type: none;
        padding: 0;
      }
      li {
        padding: 10px;
        border-bottom: 1px solid #eee;
        display: flex;
        justify-content: space-between;
      }
      li:last-child {
        border-bottom: none;
      }
      #action-select {
        width: 100%;
        padding: 8px;
        margin-bottom: 10px;
      }
    `;
    document.head.appendChild(style);

    const container = document.createElement('div');
    container.className = 'skippy-ui-container';

    const headerDiv = document.createElement('div');
    headerDiv.className = 'header';
    const logo = document.createElement('img');
    logo.src = 'https://via.placeholder.com/40x40/007bff/ffffff?text=SK';
    logo.alt = 'Skippy Logo';
    const title = document.createElement('h1');
    title.textContent = 'Skippy Concierge';
    headerDiv.appendChild(logo);
    headerDiv.appendChild(title);
    container.appendChild(headerDiv);

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
