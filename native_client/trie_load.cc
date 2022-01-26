#include <algorithm>
#include <iostream>
#include <string>

#include "ctcdecode/scorer.h"
#include "alphabet.h"

#ifdef DEBUG
#include <limits>
#include <unordered_map>
#include "ctcdecode/path_trie.h"
#endif // DEBUG

using namespace std;

#ifdef DEBUG
template<typename T>
void dfs_dumpvocab(const Alphabet& alphabet, const T& fst, int state_id = 0, string word = "")
{
  const fst::StdArc::Weight weight = fst->Final(state_id);
  const bool is_final = weight != fst::StdArc::Weight::Zero();
  if (is_final) {
    printf("%s\n", word.c_str());
  }
  for (fst::ArcIterator<fst::ConstFst<fst::StdArc>> aiter(*fst, state_id); !aiter.Done(); aiter.Next()) {
    const fst::StdArc& arc = aiter.Value();
    string arc_char = alphabet.DecodeSingle(arc.olabel - 1);
    string grown_word = word;
    grown_word += arc_char;
    dfs_dumpvocab(alphabet, fst, arc.nextstate, grown_word);
  }
}
#endif

int main(int argc, char** argv)
{
  if (argc != 4) {
    fprintf(stderr, "Usage: %s <scorer_path> <alphabet_path> [arcs|dump-vocab]\n", argv[0]);
    return 1;
  }

  const char* scorer_path   = argv[1];
  const char* alphabet_path = argv[2];
  const char* command       = argv[3];
  fprintf(stderr, "Loading scorer(%s) and alphabet(%s)\n", scorer_path, alphabet_path);

  Alphabet alphabet;
  int err = alphabet.init(alphabet_path);
  if (err != 0) {
    return err;
  }
  Scorer scorer;
  err = scorer.init(scorer_path, alphabet);
#ifndef DEBUG
  return err;
#else
  // Print some info about the FST
  using FstType = fst::ConstFst<fst::StdArc>;

  auto dict = scorer.dictionary.get();

  if (!strcmp(command, "arcs")) {
    struct state_info {
      int range_min = numeric_limits<int>::max();
      int range_max = numeric_limits<int>::min();
    };

    auto print_states_from = [&](int i) {
      unordered_map<int, state_info> sinfo;
      for (fst::ArcIterator<FstType> aiter(*dict, i); !aiter.Done(); aiter.Next()) {
        const fst::StdArc& arc = aiter.Value();
        sinfo[arc.nextstate].range_min = min(sinfo[arc.nextstate].range_min, arc.ilabel-1);
        sinfo[arc.nextstate].range_max = max(sinfo[arc.nextstate].range_max, arc.ilabel-1);
      }

      for (auto it = sinfo.begin(); it != sinfo.end(); ++it) {
        state_info s = it->second;
        printf("%d -> state %d (chars 0x%X - 0x%X, '%c' - '%c')\n", i, it->first, (unsigned int)s.range_min, (unsigned int)s.range_max, (char)s.range_min, (char)s.range_max);
      }
    };

    print_states_from(0);
  } else if (!strcmp(command, "dump-vocab")) {
    // Dump vocabulary
    dfs_dumpvocab(alphabet, dict);
  } else {
    fprintf(stderr, "No command specified.");
  }

  return 0;
#endif // DEBUG
}
