import { SCOTTISH_TEAMS } from '../teams.js';

describe('SCOTTISH_TEAMS', () => {
    test('has exactly 42 teams', () => {
        expect(SCOTTISH_TEAMS).toHaveLength(42);
    });

    test('every team has the required shape', () => {
        for (const team of SCOTTISH_TEAMS) {
            expect(typeof team.espnId).toBe('number');
            expect(typeof team.name).toBe('string');
            expect(team.name.length).toBeGreaterThan(0);
            expect(typeof team.shortName).toBe('string');
            expect(team.shortName.length).toBeGreaterThan(0);
        }
    });

    test('all espnIds are unique', () => {
        const ids = SCOTTISH_TEAMS.map(t => t.espnId);
        expect(new Set(ids).size).toBe(ids.length);
    });

    test('all names are unique', () => {
        const names = SCOTTISH_TEAMS.map(t => t.name);
        expect(new Set(names).size).toBe(names.length);
    });

    test('all espnIds are positive integers', () => {
        for (const team of SCOTTISH_TEAMS) {
            expect(Number.isInteger(team.espnId)).toBe(true);
            expect(team.espnId).toBeGreaterThan(0);
        }
    });
});
