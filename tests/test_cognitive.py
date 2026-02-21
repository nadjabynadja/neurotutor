import pytest
import numpy as np
from datetime import datetime


class TestFeatures:
    """Tests for EEG feature extraction."""

    def test_band_powers_shape(self):
        """Test band powers returns correct number of bands."""
        from cognitive.features import band_powers
        
        samples = np.random.randn(4, 512)
        powers = band_powers(samples, fs=256)
        
        assert len(powers) == 5
        assert all(band in powers for band in ["delta", "theta", "alpha", "beta", "gamma"])

    def test_relative_band_powers_sum(self):
        """Test relative band powers sum to approximately 1."""
        from cognitive.features import relative_band_powers
        
        samples = np.random.randn(4, 512)
        rel_powers = relative_band_powers(samples, fs=256)
        
        total = sum(rel_powers.values())
        assert 0.99 <= total <= 1.01

    def test_theta_beta_ratio_positive(self):
        """Test theta beta ratio is always positive."""
        from cognitive.features import theta_beta_ratio
        
        samples = np.random.randn(4, 512)
        ratio = theta_beta_ratio(samples, fs=256)
        
        assert ratio >= 0

    def test_engagement_index_positive(self):
        """Test engagement index is always positive."""
        from cognitive.features import engagement_index
        
        samples = np.random.randn(4, 512)
        index = engagement_index(samples, fs=256)
        
        assert index >= 0

    def test_spectral_entropy_normalized(self):
        """Test spectral entropy is between 0 and 1."""
        from cognitive.features import spectral_entropy
        
        samples = np.random.randn(4, 512)
        entropy = spectral_entropy(samples, fs=256)
        
        assert 0 <= entropy <= 1

    def test_frontal_asymmetry_returns_float(self):
        """Test frontal asymmetry returns a float."""
        from cognitive.features import frontal_asymmetry
        
        samples = np.random.randn(4, 512)
        asymmetry = frontal_asymmetry(samples)
        
        assert isinstance(asymmetry, float)

    def test_frontal_asymmetry_with_single_channel(self):
        """Test frontal asymmetry with single channel returns 0."""
        from cognitive.features import frontal_asymmetry
        
        samples = np.random.randn(1, 512)
        asymmetry = frontal_asymmetry(samples)
        
        assert asymmetry == 0.0

    def test_extract_features_keys(self):
        """Test extract features returns expected keys."""
        from cognitive.features import extract_features
        
        samples = np.random.randn(4, 512)
        features = extract_features(samples, fs=256)
        
        assert "theta_beta_ratio" in features
        assert "engagement_index" in features
        assert "spectral_entropy" in features
        assert "frontal_asymmetry" in features
        assert "mean_amplitude" in features
        assert "std_amplitude" in features

    def test_feature_vector_shape(self):
        """Test feature vector has correct shape."""
        from cognitive.features import extract_features, feature_vector
        
        samples = np.random.randn(4, 512)
        features = extract_features(samples, fs=256)
        vec = feature_vector(features)
        
        assert vec.ndim == 1
        assert vec.shape[0] == len(features)


class TestCognitiveState:
    """Tests for cognitive state model."""

    def test_cognitive_state_dataclass(self):
        """Test CognitiveState dataclass creation."""
        from cognitive.attention_detector import CognitiveState
        
        state = CognitiveState(
            timestamp=datetime.now(),
            cognitive_load=0.5,
            attention_level=0.8,
            engagement=0.7,
            confusion_indicator=0.3,
            fatigue_indicator=0.2,
            is_calibrated=True
        )
        
        assert state.cognitive_load == 0.5
        assert state.attention_level == 0.8

    def test_cognitive_state_to_dict(self):
        """Test CognitiveState to_dict method."""
        from cognitive.attention_detector import CognitiveState
        
        state = CognitiveState(
            timestamp=datetime.now(),
            cognitive_load=0.5,
            attention_level=0.8,
            engagement=0.7,
            confusion_indicator=0.3,
            fatigue_indicator=0.2,
            is_calibrated=True
        )
        
        d = state.to_dict()
        
        assert "cognitive_load" in d
        assert "attention_level" in d
        assert "timestamp" in d
