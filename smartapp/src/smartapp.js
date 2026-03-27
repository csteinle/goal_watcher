import SmartApp from '@smartthings/smartapp';
import { DynamoDBContextStore } from './dynamodb-context-store.js';
import { SCOTTISH_TEAMS } from './teams.js';

const contextStore = new DynamoDBContextStore({
    tableName: process.env.INSTALLATIONS_TABLE_NAME || 'goal-watcher-installations',
    region: process.env.AWS_REGION || 'us-east-1',
});

function getTeamOptions() {
    return SCOTTISH_TEAMS.map(t => ({ id: String(t.espnId), name: t.name }));
}

export const smartapp = new SmartApp()
    .enableEventLogging(2)
    .contextStore(contextStore)
    .page('teamPage', (context, page) => {
        page.name('Select Your Team');
        page.section('team', section => {
            section.enumSetting('scottishTeam')
                .name('Scottish Football Team')
                .description('Select the team you want to track for goal alerts')
                .required(true)
                .options(getTeamOptions());
        });
        page.section('competitions', section => {
            section.enumSetting('competitions')
                .name('Competitions')
                .description('Which competitions to monitor')
                .required(false)
                .multiple(true)
                .options([
                    { id: 'sco.1', name: 'Scottish Premiership' },
                    { id: 'sco.2', name: 'Scottish Championship' },
                    { id: 'sco.3', name: 'Scottish League One' },
                    { id: 'sco.4', name: 'Scottish League Two' },
                    { id: 'sco.tennents', name: 'Scottish Cup' },
                    { id: 'sco.cis', name: 'Scottish League Cup' },
                    { id: 'sco.challenge', name: 'Scottish Challenge Cup' },
                ]);
        });
    })
    .page('devicesPage', (context, page) => {
        page.name('Choose Devices');
        page.section('lights', section => {
            section.deviceSetting('goalLights')
                .name('Lights to Flash')
                .description('These lights will flash when a goal is scored')
                .capabilities(['switch'])
                .required(false)
                .multiple(true);
        });
        page.section('switches', section => {
            section.deviceSetting('goalSwitches')
                .name('Switches to Toggle')
                .description('These switches will be toggled when a goal is scored')
                .capabilities(['switch'])
                .required(false)
                .multiple(true);
        });
    })
    .installed(async (context, installData) => {
        console.log('SmartApp installed:', JSON.stringify(installData));
    })
    .updated(async (context, updateData) => {
        console.log('SmartApp updated:', JSON.stringify(updateData));
    })
    .uninstalled(async (context, uninstallData) => {
        console.log('SmartApp uninstalled:', JSON.stringify(uninstallData));
    });
