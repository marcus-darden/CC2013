import csv

with open('LearningOutcomes.csv') as f:
    reader = csv.reader(f)
    count = 0
    counts = {1: 0, 2: 0, 3: 0}
    coverage = {'Usage': 0, 'Familiarity': 0, 'Assessment': 0}
    for row in reader:
        # Read KU from LearningOutcomes.csv
        if len(row) >= 6 and row[0].strip() and not row[4].strip():
            print '{0}: {1}'.format(row[0].strip(), row[1].strip())
            #count += 1
        # Read outcomes from LearningOutcomes.csv
        if len(row) >= 6 and row[4] and row[5]:
            row[2] = int(row[2]) if len(row[2]) < 3 else row[2]
            #row[4] = int(row[4]) if len(row[4]) < 3 else row[4]
            print '{0:>3s}. {1}'.format(row[4].strip(), row[5].strip())
            count += 1
            if type(row[2]) == int:
                counts[row[2]] += 1
            if row[3].find('Familiarity') >= 0:
                coverage['Familiarity'] += 1
            if row[3].find('Usage') >= 0:
                coverage['Usage'] += 1
            if row[3].find('Assessment') >= 0:
                coverage['Assessment'] += 1
    print '{0} rows.'.format(count)
    print counts, sum(counts.values())
    print coverage, sum(coverage.values())

