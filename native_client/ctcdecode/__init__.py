import enum
from collections import namedtuple

from . import swigwrapper  # pylint: disable=import-self

# This module is built with SWIG_PYTHON_STRICT_BYTE_CHAR so we must handle
# string encoding explicitly, here and throughout this file.
__version__ = swigwrapper.__version__.decode("utf-8")

# Hack: import error codes by matching on their names, as SWIG unfortunately
# does not support binding enums to Python in a scoped manner yet.
for symbol in dir(swigwrapper):
    if symbol.startswith("STT_ERR_"):
        globals()[symbol] = getattr(swigwrapper, symbol)


class Alphabet(swigwrapper.Alphabet):
    """An Alphabet is a bidirectional map from tokens (eg. characters) to
    internal integer representations used by the underlying acoustic models
    and external scorers. It can be created from alphabet configuration file
    via the constructor, or from a list of tokens via :py:meth:`Alphabet.InitFromLabels`.
    """

    def __init__(self, config_path=None):
        super(Alphabet, self).__init__()
        if config_path:
            err = self.init(config_path.encode("utf-8"))
            if err != 0:
                raise ValueError(
                    "Alphabet initialization failed with error code 0x{:X}".format(err)
                )

    def InitFromLabels(self, data):
        """
        Initialize Alphabet from a list of labels ``data``. Each label gets
        associated with an integer value corresponding to its position in the list.
        """
        return super(Alphabet, self).InitFromLabels([c.encode("utf-8") for c in data])

    def CanEncodeSingle(self, input):
        """
        Returns true if the single character/output class has a corresponding label
        in the alphabet.
        """
        return super(Alphabet, self).CanEncodeSingle(input.encode("utf-8"))

    def CanEncode(self, input):
        """
        Returns true if the entire string can be encoded into labels in this
        alphabet.
        """
        return super(Alphabet, self).CanEncode(input.encode("utf-8"))

    def EncodeSingle(self, input):
        """
        Encode a single character/output class into a label. Character must be in
        the alphabet, this method will assert that. Use `CanEncodeSingle` to test.
        """
        return super(Alphabet, self).EncodeSingle(input.encode("utf-8"))

    def Encode(self, input):
        """
        Encode a sequence of character/output classes into a sequence of labels.
        Characters are assumed to always take a single Unicode codepoint.
        Characters must be in the alphabet, this method will assert that. Use
        ``CanEncode`` and ``CanEncodeSingle`` to test.
        """
        # Convert SWIG's UnsignedIntVec to a Python list
        res = super(Alphabet, self).Encode(input.encode("utf-8"))
        return [el for el in res]

    def DecodeSingle(self, input):
        res = super(Alphabet, self).DecodeSingle(input)
        return res.decode("utf-8")

    def Decode(self, input):
        """Decode a sequence of labels into a string."""
        res = super(Alphabet, self).Decode(input)
        return res.decode("utf-8")


class Scorer(swigwrapper.Scorer):
    """An external scorer is a data structure composed of a language model built
        from text data, as well as the vocabulary used in the construction of this
        language model and additional parameters related to how the decoding
        process uses the external scorer, such as the language model weight
        ``alpha`` and the word insertion score ``beta``.

    :param alpha: Language model weight.
    :type alpha: float
    :param beta: Word insertion score.
    :type beta: float
    :param scorer_path: Path to load scorer from.
    :type scorer_path: str
    :param alphabet: Alphabet object matching the tokens used when creating the
                     external scorer.
    :type alphabet: Alphabet
    """

    def __init__(self, alpha=None, beta=None, scorer_path=None, alphabet=None):
        super(Scorer, self).__init__()
        # Allow bare initialization
        if alphabet:
            assert alpha is not None, "alpha parameter is required"
            assert beta is not None, "beta parameter is required"
            assert scorer_path, "scorer_path parameter is required"

            err = self.init_from_filepath(scorer_path.encode("utf-8"), alphabet)
            if err != 0:
                raise ValueError(
                    "Scorer initialization failed with error code 0x{:X}".format(err)
                )

            self.reset_params(alpha, beta)


DecodeResult = namedtuple(
    "DecodeResult", ["confidence", "transcript", "tokens", "timesteps"]
)


def ctc_beam_search_decoder(
    probs_seq,
    alphabet,
    beam_size,
    cutoff_prob=1.0,
    cutoff_top_n=40,
    scorer=None,
    hot_words=dict(),
    num_results=1,
):
    """Wrapper for the CTC Beam Search Decoder.

    :param probs_seq: 2-D list of probability distributions over each time
                      step, with each element being a list of normalized
                      probabilities over alphabet and blank.
    :type probs_seq: 2-D list
    :param alphabet: Alphabet
    :param beam_size: Width for beam search.
    :type beam_size: int
    :param cutoff_prob: Cutoff probability in pruning,
                        default 1.0, no pruning.
    :type cutoff_prob: float
    :param cutoff_top_n: Cutoff number in pruning, only top cutoff_top_n
                         characters with highest probs in alphabet will be
                         used in beam search, default 40.
    :type cutoff_top_n: int
    :param scorer: External scorer for partially decoded sentence, e.g. word
                   count or language model.
    :type scorer: Scorer
    :param hot_words: Map of words (keys) to their assigned boosts (values)
    :type hot_words: dict[string, float]
    :param num_results: Number of beams to return.
    :type num_results: int
    :return: List of tuples of confidence and sentence as decoding
             results, in descending order of the confidence.
    :rtype: list
    """
    beam_results = swigwrapper.ctc_beam_search_decoder(
        probs_seq,
        alphabet,
        beam_size,
        cutoff_prob,
        cutoff_top_n,
        scorer,
        hot_words,
        num_results,
    )
    beam_results = [
        DecodeResult(
            res.confidence,
            alphabet.Decode(res.tokens),
            [int(t) for t in res.tokens],
            [int(t) for t in res.timesteps],
        )
        for res in beam_results
    ]
    return beam_results


def ctc_beam_search_decoder_for_wav2vec2am(
    probs_seq,
    alphabet,
    beam_size,
    cutoff_prob=1.0,
    cutoff_top_n=40,
    blank_id=-1,
    ignored_symbols=frozenset(),
    scorer=None,
    hot_words=dict(),
    num_results=1,
):
    """Wrapper for the CTC Beam Search Decoder.

    :param probs_seq: 2-D list of probability distributions over each time
                      step, with each element being a list of normalized
                      probabilities over alphabet and blank.
    :type probs_seq: 2-D list
    :param alphabet: Alphabet
    :param beam_size: Width for beam search.
    :type beam_size: int
    :param cutoff_prob: Cutoff probability in pruning,
                        default 1.0, no pruning.
    :type cutoff_prob: float
    :param cutoff_top_n: Cutoff number in pruning, only top cutoff_top_n
                         characters with highest probs in alphabet will be
                         used in beam search, default 40.
    :type cutoff_top_n: int
    :param scorer: External scorer for partially decoded sentence, e.g. word
                   count or language model.
    :type scorer: Scorer
    :param hot_words: Map of words (keys) to their assigned boosts (values)
    :type hot_words: dict[string, float]
    :param num_results: Number of beams to return.
    :type num_results: int
    :return: List of tuples of confidence and sentence as decoding
             results, in descending order of the confidence.
    :rtype: list
    """
    beam_results = swigwrapper.ctc_beam_search_decoder_for_wav2vec2am(
        probs_seq,
        alphabet,
        beam_size,
        cutoff_prob,
        cutoff_top_n,
        blank_id,
        ignored_symbols,
        scorer,
        hot_words,
        num_results,
    )
    beam_results = [
        DecodeResult(
            res.confidence,
            alphabet.Decode(res.tokens),
            [int(t) for t in res.tokens],
            [int(t) for t in res.timesteps],
        )
        for res in beam_results
    ]
    return beam_results


def ctc_beam_search_decoder_batch(
    probs_seq,
    seq_lengths,
    alphabet,
    beam_size,
    num_processes,
    cutoff_prob=1.0,
    cutoff_top_n=40,
    scorer=None,
    hot_words=dict(),
    num_results=1,
):
    """Wrapper for the batched CTC beam search decoder.

    :param probs_seq: 3-D list with each element as an instance of 2-D list
                      of probabilities used by ctc_beam_search_decoder().
    :type probs_seq: 3-D list
    :param alphabet: alphabet list.
    :alphabet: Alphabet
    :param beam_size: Width for beam search.
    :type beam_size: int
    :param num_processes: Number of parallel processes.
    :type num_processes: int
    :param cutoff_prob: Cutoff probability in alphabet pruning,
                        default 1.0, no pruning.
    :type cutoff_prob: float
    :param cutoff_top_n: Cutoff number in pruning, only top cutoff_top_n
                         characters with highest probs in alphabet will be
                         used in beam search, default 40.
    :type cutoff_top_n: int
    :param num_processes: Number of parallel processes.
    :type num_processes: int
    :param scorer: External scorer for partially decoded sentence, e.g. word
                   count or language model.
    :type scorer: Scorer
    :param hot_words: Map of words (keys) to their assigned boosts (values)
    :type hot_words: dict[string, float]
    :param num_results: Number of beams to return.
    :type num_results: int
    :return: List of tuples of confidence and sentence as decoding
             results, in descending order of the confidence.
    :rtype: list
    """
    batch_beam_results = swigwrapper.ctc_beam_search_decoder_batch(
        probs_seq,
        seq_lengths,
        alphabet,
        beam_size,
        num_processes,
        cutoff_prob,
        cutoff_top_n,
        scorer,
        hot_words,
        num_results,
    )
    batch_beam_results = [
        [
            DecodeResult(
                res.confidence,
                alphabet.Decode(res.tokens),
                [int(t) for t in res.tokens],
                [int(t) for t in res.timesteps],
            )
            for res in beam_results
        ]
        for beam_results in batch_beam_results
    ]
    return batch_beam_results


def ctc_beam_search_decoder_for_wav2vec2am_batch(
    probs_seq,
    seq_lengths,
    alphabet,
    beam_size,
    num_threads,
    cutoff_prob=1.0,
    cutoff_top_n=40,
    blank_id=-1,
    ignored_symbols=frozenset(),
    scorer=None,
    hot_words=dict(),
    num_results=1,
):
    """Wrapper for the batched CTC beam search decoder for wav2vec2 AM.

    :param probs_seq: 3-D list with each element as an instance of 2-D list
                      of probabilities used by ctc_beam_search_decoder().
    :type probs_seq: 3-D list
    :param alphabet: alphabet list.
    :alphabet: Alphabet
    :param beam_size: Width for beam search.
    :type beam_size: int
    :param num_threads: Number of threads to use for processing batch.
    :type num_threads: int
    :param cutoff_prob: Cutoff probability in alphabet pruning,
                        default 1.0, no pruning.
    :type cutoff_prob: float
    :param cutoff_top_n: Cutoff number in pruning, only top cutoff_top_n
                         characters with highest probs in alphabet will be
                         used in beam search, default 40.
    :type cutoff_top_n: int
    :param scorer: External scorer for partially decoded sentence, e.g. word
                   count or language model.
    :type scorer: Scorer
    :param hot_words: Map of words (keys) to their assigned boosts (values)
    :type hot_words: dict[string, float]
    :param num_results: Number of beams to return.
    :type num_results: int
    :return: List of tuples of confidence and sentence as decoding
             results, in descending order of the confidence.
    :rtype: list
    """
    batch_beam_results = swigwrapper.ctc_beam_search_decoder_for_wav2vec2am_batch(
        probs_seq,
        seq_lengths,
        alphabet,
        beam_size,
        num_threads,
        cutoff_prob,
        cutoff_top_n,
        blank_id,
        ignored_symbols,
        scorer,
        hot_words,
        num_results,
    )
    batch_beam_results = [
        [
            DecodeResult(
                res.confidence,
                alphabet.Decode(res.tokens),
                [int(t) for t in res.tokens],
                [int(t) for t in res.timesteps],
            )
            for res in beam_results
        ]
        for beam_results in batch_beam_results
    ]
    return batch_beam_results


class FlashlightDecoderState(swigwrapper.FlashlightDecoderState):
    """
    This class contains constants used to specify the desired behavior for the
    :py:func:`flashlight_beam_search_decoder` and :py:func:`flashlight_beam_search_decoder_batch`
    functions.
    """

    class CriterionType(enum.IntEnum):
        """Constants used to specify which loss criterion was used by the
        acoustic model. This class is a Python :py:class:`enum.IntEnum`.
        """

        #: Decoder mode for handling acoustic models trained with CTC loss
        CTC = swigwrapper.FlashlightDecoderState.CTC

        #: Decoder mode for handling acoustic models trained with ASG loss
        ASG = swigwrapper.FlashlightDecoderState.ASG

        #: Decoder mode for handling acoustic models trained with Seq2seq loss
        #: Note: this criterion type is currently not supported.
        S2S = swigwrapper.FlashlightDecoderState.S2S

    class DecoderType(enum.IntEnum):
        """Constants used to specify if decoder should operate in lexicon mode,
        only predicting words present in a fixed vocabulary, or in lexicon-free
        mode, without such restriction. This class is a Python :py:class:`enum.IntEnum`.
        """

        #: Lexicon mode, only predict words in specified vocabulary.
        LexiconBased = swigwrapper.FlashlightDecoderState.LexiconBased

        #: Lexicon-free mode, allow prediction of any word.
        LexiconFree = swigwrapper.FlashlightDecoderState.LexiconFree

    class TokenType(enum.IntEnum):
        """Constants used to specify the granularity of text units used when training
        the external scorer in relation to the text units used when training the
        acoustic model. For example, you can have an acoustic model predicting
        characters and an external scorer trained on words, or an acoustic model
        and an external scorer both trained with sub-word units. If the acoustic
        model and the scorer were both trained on the same text unit granularity,
        use ``TokenType.Single``. Otherwise, if the external scorer was trained
        on a sequence of acoustic model text units, use ``TokenType.Aggregate``.
        This class is a Python :py:class:`enum.IntEnum`.
        """

        #: Token type for external scorers trained on the same textual units as
        #: the acoustic model.
        Single = swigwrapper.FlashlightDecoderState.Single

        #: Token type for external scorers trained on a sequence of acoustic model
        #: textual units.
        Aggregate = swigwrapper.FlashlightDecoderState.Aggregate


def flashlight_beam_search_decoder(
    logits_seq,
    alphabet,
    beam_size,
    decoder_type,
    token_type,
    lm_tokens,
    scorer=None,
    beam_threshold=25.0,
    cutoff_top_n=40,
    silence_score=0.0,
    merge_with_log_add=False,
    criterion_type=FlashlightDecoderState.CriterionType.CTC,
    transitions=[],
    num_results=1,
):
    """Decode acoustic model emissions for a single sample. Note that unlike
        :py:func:`ctc_beam_search_decoder`, this function expects raw outputs
        from CTC and ASG acoustic models, without softmaxing them over
        timesteps.

    :param logits_seq: 2-D list of acoustic model emissions, dimensions are
                       time steps x number of output units.
    :type logits_seq: 2-D list of floats or numpy array
    :param alphabet: Alphabet object matching the tokens used when creating the
                     acoustic model and external scorer if specified.
    :type alphabet: Alphabet
    :param beam_size: Width for beam search.
    :type beam_size: int
    :param decoder_type: Decoding mode, lexicon-constrained or lexicon-free.
    :type decoder_type: FlashlightDecoderState.DecoderType
    :param token_type: Type of token in the external scorer.
    :type token_type: FlashlightDecoderState.TokenType
    :param lm_tokens: List of tokens to constrain decoding to when in lexicon-constrained
                      mode. Must match the token type used in the scorer, ie.
                      must be a list of characters if scorer is character-based,
                      or a list of words if scorer is word-based.
    :param lm_tokens: list[str]
    :param scorer: External scorer.
    :type scorer: Scorer
    :param beam_threshold: Maximum threshold in beam score from leading beam. Any
                           newly created candidate beams which lag behind the best
                           beam so far by more than this value will get pruned.
                           This is a performance optimization parameter and an
                           appropriate value should be found empirically using a
                           validation set.
    :type beam_threshold: float
    :param cutoff_top_n: Maximum number of tokens to expand per time step during
                         decoding. Only the highest probability cutoff_top_n
                         candidates (characters, sub-word units, words) in a given
                         timestep will be expanded. This is a performance
                         optimization parameter and an appropriate value should
                         be found empirically using a validation set.
    :type cutoff_top_n: int
    :param silence_score: Score to add to beam when encountering a predicted
                          silence token (eg. the space symbol).
    :type silence_score: float
    :param merge_with_log_add: Whether to use log-add when merging scores of
                               new candidate beams equivalent to existing ones
                               (leading to the same transcription). When disabled,
                               the maximum score is used.
    :type merge_with_log_add: bool
    :param criterion_type: Criterion used for training the acoustic model.
    :type criterion_type: FlashlightDecoderState.CriterionType
    :param transitions: Transition score matrix for ASG acoustic models.
    :type transitions: list[float]
    :param num_results: Number of beams to return.
    :type num_results: int
    :return: List of FlashlightOutput structures.
    :rtype: list[FlashlightOutput]
    """
    return swigwrapper.flashlight_beam_search_decoder(
        logits_seq,
        alphabet,
        beam_size,
        beam_threshold,
        cutoff_top_n,
        scorer,
        token_type,
        lm_tokens,
        decoder_type,
        silence_score,
        merge_with_log_add,
        criterion_type,
        transitions,
        num_results,
    )


def flashlight_beam_search_decoder_batch(
    probs_seq,
    seq_lengths,
    alphabet,
    beam_size,
    decoder_type,
    token_type,
    lm_tokens,
    num_processes,
    scorer=None,
    beam_threshold=25.0,
    cutoff_top_n=40,
    silence_score=0.0,
    merge_with_log_add=False,
    criterion_type=FlashlightDecoderState.CriterionType.CTC,
    transitions=[],
    num_results=1,
):
    """Decode batch acoustic model emissions in parallel. ``num_processes``
    controls how many samples from the batch will be decoded simultaneously.
    All the other parameters are forwarded to :py:func:`flashlight_beam_search_decoder`.

    Returns a list of lists of FlashlightOutput structures.
    """

    return swigwrapper.flashlight_beam_search_decoder_batch(
        probs_seq,
        seq_lengths,
        alphabet,
        beam_size,
        beam_threshold,
        cutoff_top_n,
        scorer,
        token_type,
        lm_tokens,
        decoder_type,
        silence_score,
        merge_with_log_add,
        criterion_type,
        transitions,
        num_results,
        num_processes,
    )


class UTF8Alphabet(swigwrapper.UTF8Alphabet):
    """Alphabet class representing 255 possible byte values for Bytes Output Mode.
    For internal use only.
    """

    def __init__(self):
        super(UTF8Alphabet, self).__init__()
        err = self.init(b"")
        if err != 0:
            raise ValueError(
                "UTF8Alphabet initialization failed with error code 0x{:X}".format(err)
            )

    def CanEncodeSingle(self, input):
        """
        Returns true if the single character/output class has a corresponding label
        in the alphabet.
        """
        return super(UTF8Alphabet, self).CanEncodeSingle(input.encode("utf-8"))

    def CanEncode(self, input):
        """
        Returns true if the entire string can be encoded into labels in this
        alphabet.
        """
        return super(UTF8Alphabet, self).CanEncode(input.encode("utf-8"))

    def EncodeSingle(self, input):
        """
        Encode a single character/output class into a label. Character must be in
        the alphabet, this method will assert that. Use ``CanEncodeSingle`` to test.
        """
        return super(UTF8Alphabet, self).EncodeSingle(input.encode("utf-8"))

    def Encode(self, input):
        """
        Encode a sequence of character/output classes into a sequence of labels.
        Characters are assumed to always take a single Unicode codepoint.
        Characters must be in the alphabet, this method will assert that. Use
        ``CanEncode`` and ``CanEncodeSingle`` to test.
        """
        # Convert SWIG's UnsignedIntVec to a Python list
        res = super(UTF8Alphabet, self).Encode(input.encode("utf-8"))
        return [el for el in res]

    def DecodeSingle(self, input):
        res = super(UTF8Alphabet, self).DecodeSingle(input)
        return res.decode("utf-8")

    def Decode(self, input):
        """Decode a sequence of labels into a string."""
        res = super(UTF8Alphabet, self).Decode(input)
        return res.decode("utf-8")
