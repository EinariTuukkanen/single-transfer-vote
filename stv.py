import sys
import csv

# Number of candidates to choose
N_SEATS = 3

# Tie error to account for rounding erros when summing fractions
TIE_ERROR = 1e-10

filename = sys.argv[1]
candidates = []
ballots = []
passed = []
eliminated = []


class Ballot:
    def __init__(self, votes):
        self.votes = votes
        self.original_votes = votes[:]
        self.weight = 1.0

    def next_vote(self):
        return next(iter(self.votes), None), self.weight

    def __str__(self):
        return " ".join([f"({v})" for v in self.votes]) + f", value = {self.weight}"


with open(filename, "r", encoding='utf-8') as f:
    votereader = csv.reader(f, delimiter=",", quotechar='"')
    first_row = True
    for row in votereader:
        row = row[1:]  # Skip the timestamp column from google forms
        if first_row:
            # Use first row to name the candidates
            candidates = [c for c in row]
            first_row = False
        else:
            # Convert the votes into ordered list; favorite candidate is first
            ordered_votes = []
            for i in range(1, len(candidates) + 1):
                i = str(i)  # CSV returns the numbers as strings
                if i not in row:
                    # If index is left out in the middle just skip it
                    # i.e. it is not possible to give just 1 vote and 3 vote
                    continue
                # Use the ordered candidate list to map the name
                ordered_votes.append(candidates[row.index(i)])
            ballots.append(Ballot(ordered_votes))


# (number of votes)/(number of seats + 1) rounded up to two decimal places
quota = round((len(ballots) / (N_SEATS + 1)), 2)  # Old quota
print(
    f"Candidates={len(candidates)} Seats={N_SEATS} Votes={len(ballots)} Quota={quota}"
)

round_num = 0
while len(passed) < N_SEATS:
    # Clean up passed and eliminated votes
    for ballot in ballots:
        ballot.votes = [
            v for v in ballot.votes if v not in passed and v not in eliminated
        ]

    # Calculate votes remaining for this round (does not include zero votes)
    active_votes = {}
    for ballot in ballots:
        candidate, weight = ballot.next_vote()
        if candidate is not None:
            if candidate not in active_votes:
                active_votes[candidate] = {"vote_sum": 0, "ballots": []}
            active_votes[candidate]["vote_sum"] += weight
            active_votes[candidate]["ballots"].append(ballot)

    # Update quota ?
    # active_vote_count = sum([len(v['ballots']) for v in active_votes.values()])
    # quota = active_vote_count / (N_SEATS + 1) + 1  # Droop quota
    # quota = round((active_vote_count / (N_SEATS + 1)), 2)  # Old quota

    # Sorted dictitems list
    sorted_active_votes = sorted(
        active_votes.items(), key=lambda x: x[1]["vote_sum"], reverse=True
    )

    # Print round information
    round_num += 1
    input(f"\nPress <enter> to continue to round {round_num}\n")
    print(f"--- ROUND {round_num} ---")

    print("\n[Ballots and their values]")
    for i, ballot in enumerate(ballots):
        print(f"vote {i + 1}: {str(ballot)}")

    print("\n[Candidates and their vote sums]")
    for candidate in candidates:
        votes = dict(sorted_active_votes).get(candidate, {}).get("vote_sum", 0)
        print(f"{candidate} = {round(votes, 2)}")

    print("\n[Status so far]")
    print(f"Passed: {passed}")
    print(f"Eliminated: {eliminated}")

    # Get the best candidate (first in sorted list)
    best_candidate, best_active = list(sorted_active_votes)[0]

    new_passed = False
    best_vote_sum = best_active["vote_sum"]
    if best_vote_sum >= quota:
        print("\n[Quota exceeded]")
        print(f"Highest vote count = {best_vote_sum}")
        # NOTE: summing fractions tends to result in rounding erros, hence we use TIE_ERROR to find true equals
        # TODO: consider converting values to actual fracion class to enable exact comparisons
        best_candidates = [
            c for c, a in sorted_active_votes if abs(a["vote_sum"] - best_vote_sum) < TIE_ERROR
        ]
        print(
            f"Number of candidates with the highest vote count = {len(best_candidates)}"
        )
        if len(best_candidates) > 1:
            print("\n[Winner tie]")
            print(f"Winner tie between {best_candidates}")
            tiebreak_winner = input("Choose the one to PASS: ")
            best_candidate, best_active = next(
                (c, a) for c, a in sorted_active_votes if c == tiebreak_winner
            )

        passed.append(best_candidate)
        new_weight = (best_vote_sum - quota) / best_vote_sum
        for ballot in best_active["ballots"]:
            ballot.weight *= new_weight
        new_passed = True
        print(f"\n>>> Candidate elected = {best_candidate}")
        print(f"Reallocating surplus = {round(new_weight, 5)}")

    if new_passed:
        # Continue to calculate excess votes
        continue

    worst_candidate, worst_active = list(sorted_active_votes)[-1]
    worst_vote_sum = worst_active["vote_sum"]
    worst_candidates = [
        c for c, a in sorted_active_votes if a["vote_sum"] == worst_vote_sum
    ]
    print("\n[Quota not exceeded]")
    print(f"Fewest vote count = {worst_vote_sum}")
    print(f"Number of candidates with the fewest vote count = {len(worst_candidates)}")
    if len(worst_candidates) > 1:
        print("\n[Loser tie]")
        print(f"Loser tie between {worst_candidates}")
        tiebreak_loser = input("Choose the one to DROP: ")
        worst_candidate, worst_active = next(
            (c, a) for c, a in sorted_active_votes if c == tiebreak_loser
        )
    eliminated.append(worst_candidate)
    print(f"\n>>> Candidate eliminated = {worst_candidate}")

    zero_elims = []
    for candidate in candidates:
        active_candidates = [c for c, _ in sorted_active_votes]
        if (
            candidate not in active_candidates
            and candidate not in eliminated
            and candidate not in passed
        ):
            zero_elims.append(candidate)
    if len(zero_elims):
        print(f"Eliminating candidates with zero votes = {zero_elims}")
        eliminated += zero_elims

print("\n--- FINISHED ---\n")

print(f"Eliminated: {eliminated}\n")
print(f"Elected: {passed}\n")
