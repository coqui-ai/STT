#ifndef ALPHABET_H
#define ALPHABET_H

#include <string>
#include <unordered_map>
#include <vector>

#include "flashlight/lib/text/dictionary/Dictionary.h"

/*
 * Loads a text file describing a mapping of labels to strings, one string per
 * line. This is used by the decoder, client and Python scripts to convert the
 * output of the decoder to a human-readable string and vice-versa.
 */
class Alphabet : public fl::lib::text::Dictionary
{
public:
  Alphabet() = default;
  Alphabet(const Alphabet&) = default;
  Alphabet& operator=(const Alphabet&) = default;
  virtual ~Alphabet() = default;

  virtual int init(const char *config_file);

  // Initialize directly from sequence of labels.
  void InitFromLabels(const std::vector<std::string>& labels);

  // Serialize alphabet into a binary buffer.
  std::string Serialize();

  // Serialize alphabet into a text representation (ie. config file read by `init`)
  std::string SerializeText();

  // Deserialize alphabet from a binary buffer.
  int Deserialize(const char* buffer, const int buffer_size);

  size_t GetSize() const;

  bool IsSpace(unsigned int index) const {
    return index == space_index_;
  }

  unsigned int GetSpaceLabel() const {
    return space_index_;
  }

  virtual std::vector<std::string> GetLabels() const;

  // Returns true if the single character/output class has a corresponding index
  // in the alphabet.
  virtual bool CanEncodeSingle(const std::string& label) const;

  // Returns true if the entire string can be encoded with this alphabet.
  virtual bool CanEncode(const std::string& label) const;

  // Decode a single index into its label.
  std::string DecodeSingle(unsigned int index) const;

  // Encode a single character/output class into its index. Character must be in
  // the alphabet, this method will assert that. Use `CanEncodeSingle` to test.
  unsigned int EncodeSingle(const std::string& label) const;

  // Decode a sequence of indices into a string.
  std::string Decode(const std::vector<unsigned int>& indices) const;

  // We provide a C-style overload for accepting NumPy arrays as input, since
  // the NumPy library does not have built-in typemaps for std::vector<T>.
  std::string Decode(const unsigned int* indices, int length) const;

  // Encode a sequence of character/output classes into a sequence of indices.
  // Characters are assumed to always take a single Unicode codepoint.
  // Characters must be in the alphabet, this method will assert that. Use
  // `CanEncode` and `CanEncodeSingle` to test.
  virtual std::vector<unsigned int> Encode(const std::string& labels) const;

protected:
  unsigned int space_index_;
};

class UTF8Alphabet : public Alphabet
{
public:
  UTF8Alphabet() {
    // 255 byte values, index n -> byte value n+1
    // because NUL is never used, we don't use up an index in the maps for it
    for (int idx = 0; idx < 255; ++idx) {
      std::string val(1, idx+1);
      addEntry(val, idx);
    }
    space_index_ = ' ' - 1;
  }

  int init(const char*) override {
    return 0;
  }

  bool CanEncodeSingle(const std::string& label) const override;
  bool CanEncode(const std::string& label) const override;
  std::vector<unsigned int> Encode(const std::string& label) const override;
};

#endif //ALPHABET_H
