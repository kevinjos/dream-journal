from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Dream, Quality


class SecurityTestCase(APITestCase):
    """Test security implementation to ensure users cannot access each other's data."""
    
    def setUp(self) -> None:
        """Set up test users and data."""
        # Create two users
        self.user_a = User.objects.create_user(
            username='user_a',
            email='a@example.com',
            password='password123'
        )
        self.user_b = User.objects.create_user(
            username='user_b', 
            email='b@example.com',
            password='password123'
        )
        
        # Create qualities for each user
        self.quality_a1 = Quality.objects.create(user=self.user_a, name='flying')
        self.quality_a2 = Quality.objects.create(user=self.user_a, name='water')
        self.quality_b1 = Quality.objects.create(user=self.user_b, name='nightmare')
        
        # Create dreams for each user
        self.dream_a = Dream.objects.create(
            user=self.user_a,
            description='I was flying over water'
        )
        self.dream_a.qualities.add(self.quality_a1, self.quality_a2)
        
        self.dream_b = Dream.objects.create(
            user=self.user_b,
            description='Had a nightmare'
        )
        self.dream_b.qualities.add(self.quality_b1)
        
        # Update frequencies
        self.quality_a1.update_frequency()
        self.quality_a2.update_frequency()
        self.quality_b1.update_frequency()
        
        self.client = APIClient()
    
    def test_user_a_cannot_access_user_b_dreams(self) -> None:
        """Test that User A cannot access User B's dreams."""
        self.client.force_authenticate(user=self.user_a)
        
        # Try to access User B's dream
        response = self.client.get(f'/api/dreams/{self.dream_b.pk}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_user_a_cannot_access_user_b_qualities(self) -> None:
        """Test that User A cannot access User B's qualities."""
        self.client.force_authenticate(user=self.user_a)
        
        # Try to access User B's quality
        response = self.client.get(f'/api/qualities/{self.quality_b1.pk}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_user_a_can_access_own_dreams(self) -> None:
        """Test that User A can access their own dreams."""
        self.client.force_authenticate(user=self.user_a)
        
        response = self.client.get(f'/api/dreams/{self.dream_a.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.dream_a.pk)
    
    def test_user_a_can_access_own_qualities(self) -> None:
        """Test that User A can access their own qualities.""" 
        self.client.force_authenticate(user=self.user_a)
        
        response = self.client.get(f'/api/qualities/{self.quality_a1.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.quality_a1.pk)
    
    def test_dream_list_filters_by_user(self) -> None:
        """Test that dream list only shows user's own dreams."""
        self.client.force_authenticate(user=self.user_a)
        
        response = self.client.get('/api/dreams/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # DRF always paginates when DEFAULT_PAGINATION_CLASS is set
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.dream_a.pk)
    
    def test_quality_list_filters_by_user(self) -> None:
        """Test that quality list only shows user's own qualities."""
        self.client.force_authenticate(user=self.user_a)
        
        response = self.client.get('/api/qualities/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # DRF always paginates when DEFAULT_PAGINATION_CLASS is set
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        results = response.data['results']
        self.assertEqual(len(results), 2)
        quality_ids = [q['id'] for q in results]
        self.assertIn(self.quality_a1.pk, quality_ids)
        self.assertIn(self.quality_a2.pk, quality_ids)
        self.assertNotIn(self.quality_b1.pk, quality_ids)
    
    def test_unauthenticated_access_denied(self) -> None:
        """Test that unauthenticated users are denied access."""
        response = self.client.get('/api/dreams/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        response = self.client.get('/api/qualities/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class QualityGraphTestCase(TestCase):
    """Test the quality graph functionality."""
    
    def setUp(self) -> None:
        """Set up test user and data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='password123'
        )
        
        # Create qualities
        self.flying = Quality.objects.create(user=self.user, name='flying')
        self.water = Quality.objects.create(user=self.user, name='water')
        self.lucid = Quality.objects.create(user=self.user, name='lucid')
        
        # Create dreams with quality relationships
        self.dream1 = Dream.objects.create(user=self.user, description='Flying over water')
        self.dream1.qualities.add(self.flying, self.water)
        
        self.dream2 = Dream.objects.create(user=self.user, description='Lucid flying dream')
        self.dream2.qualities.add(self.flying, self.lucid)
        
        self.dream3 = Dream.objects.create(user=self.user, description='Swimming lucidly')
        self.dream3.qualities.add(self.water, self.lucid)
        
        # Update frequencies
        for quality in [self.flying, self.water, self.lucid]:
            quality.update_frequency()
    
    def test_quality_frequencies(self) -> None:
        """Test that quality frequencies are calculated correctly."""
        self.flying.refresh_from_db()
        self.water.refresh_from_db() 
        self.lucid.refresh_from_db()
        
        self.assertEqual(self.flying.frequency, 2)  # dreams 1, 2
        self.assertEqual(self.water.frequency, 2)   # dreams 1, 3
        self.assertEqual(self.lucid.frequency, 2)   # dreams 2, 3
    
    def test_quality_connections(self) -> None:
        """Test that quality connections are calculated correctly."""
        connections = self.flying.get_connections()
        
        # Flying should connect to both water and lucid
        self.assertEqual(len(connections), 2)
        
        connection_names = {conn.quality_name for conn in connections}
        self.assertEqual(connection_names, {'water', 'lucid'})
        
        # Each connection should have strength of 1 (one shared dream each)
        for conn in connections:
            self.assertEqual(conn.connection_strength, 1)
    
    def test_build_quality_graph(self) -> None:
        """Test building the complete quality graph."""
        graph = Dream.build_quality_graph(self.user)
        
        # Should have 3 nodes
        self.assertEqual(len(graph.nodes), 3)
        
        # Each quality should be present
        quality_names = {node.quality_name for node in graph.nodes.values()}
        self.assertEqual(quality_names, {'flying', 'water', 'lucid'})
        
        # Check edges for flying quality
        flying_node = next(node for node in graph.nodes.values() if node.quality_name == 'flying')
        self.assertEqual(len(flying_node.edges), 2)  # Connected to water and lucid
    
    def test_get_quality_statistics(self) -> None:
        """Test getting quality statistics for visualization."""
        stats = Dream.get_quality_statistics(self.user)
        
        # Should return statistics for all 3 qualities
        self.assertEqual(len(stats), 3)
        
        # Each statistic should have the right structure
        for stat in stats:
            self.assertIn('id', stat.__dict__)
            self.assertIn('name', stat.__dict__)
            self.assertIn('frequency', stat.__dict__)
            self.assertIn('total_connections', stat.__dict__)
            self.assertIn('top_connections', stat.__dict__)
            
            # Each quality should have 2 connections (triangle graph)
            self.assertEqual(stat.total_connections, 2)
            self.assertEqual(stat.frequency, 2)


class NestedRoutesSecurityTestCase(APITestCase):
    """Test security for nested routes: /api/dreams/{id}/qualities/{id}/"""
    
    def setUp(self) -> None:
        """Set up test users and data."""
        # Create two users
        self.user_a = User.objects.create_user(
            username='user_a',
            password='password123'
        )
        self.user_b = User.objects.create_user(
            username='user_b',
            password='password123'
        )
        
        # Create data for User A
        self.quality_a = Quality.objects.create(user=self.user_a, name='flying')
        self.dream_a = Dream.objects.create(user=self.user_a, description='Flying dream')
        
        # Create data for User B  
        self.quality_b = Quality.objects.create(user=self.user_b, name='nightmare')
        self.dream_b = Dream.objects.create(user=self.user_b, description='Bad dream')
        self.dream_b.qualities.add(self.quality_b)
        
        self.client = APIClient()
    
    def test_user_cannot_list_other_user_dream_qualities(self) -> None:
        """Test User A cannot list qualities of User B's dream."""
        self.client.force_authenticate(user=self.user_a)
        
        response = self.client.get(f'/api/dreams/{self.dream_b.pk}/qualities/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_user_can_list_own_dream_qualities(self) -> None:
        """Test User A can list qualities of their own dream."""
        self.client.force_authenticate(user=self.user_a)
        self.dream_a.qualities.add(self.quality_a)
        
        response = self.client.get(f'/api/dreams/{self.dream_a.pk}/qualities/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'flying')
    
    def test_user_cannot_add_quality_to_other_user_dream(self) -> None:
        """Test User A cannot add quality to User B's dream."""
        self.client.force_authenticate(user=self.user_a)
        
        response = self.client.put(f'/api/dreams/{self.dream_b.pk}/qualities/{self.quality_a.pk}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_user_cannot_add_other_user_quality_to_own_dream(self) -> None:
        """Test User A cannot add User B's quality to their own dream."""
        self.client.force_authenticate(user=self.user_a)
        
        response = self.client.put(f'/api/dreams/{self.dream_a.pk}/qualities/{self.quality_b.pk}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_user_can_add_own_quality_to_own_dream(self) -> None:
        """Test User A can add their own quality to their own dream."""
        self.client.force_authenticate(user=self.user_a)
        
        response = self.client.put(f'/api/dreams/{self.dream_a.pk}/qualities/{self.quality_a.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify quality was added
        self.dream_a.refresh_from_db()
        self.assertTrue(self.dream_a.qualities.filter(pk=self.quality_a.pk).exists())
    
    def test_user_cannot_remove_quality_from_other_user_dream(self) -> None:
        """Test User A cannot remove quality from User B's dream."""
        self.client.force_authenticate(user=self.user_a)
        
        response = self.client.delete(f'/api/dreams/{self.dream_b.pk}/qualities/{self.quality_b.pk}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_user_can_remove_quality_from_own_dream(self) -> None:
        """Test User A can remove quality from their own dream.""" 
        self.client.force_authenticate(user=self.user_a)
        self.dream_a.qualities.add(self.quality_a)
        
        response = self.client.delete(f'/api/dreams/{self.dream_a.pk}/qualities/{self.quality_a.pk}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify quality was removed
        self.dream_a.refresh_from_db()
        self.assertFalse(self.dream_a.qualities.filter(pk=self.quality_a.pk).exists())
    
    def test_cross_user_attack_scenarios(self) -> None:
        """Test various attack scenarios across user boundaries."""
        self.client.force_authenticate(user=self.user_a)
        
        # Scenario 1: Try to use User B's dream ID with User A's quality ID
        response = self.client.put(f'/api/dreams/{self.dream_b.pk}/qualities/{self.quality_a.pk}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Scenario 2: Try to use User A's dream ID with User B's quality ID
        response = self.client.put(f'/api/dreams/{self.dream_a.pk}/qualities/{self.quality_b.pk}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Scenario 3: Try to use both User B's IDs
        response = self.client.put(f'/api/dreams/{self.dream_b.pk}/qualities/{self.quality_b.pk}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_quality_frequency_updates_correctly(self) -> None:
        """Test that quality frequencies update correctly when using nested routes."""
        self.client.force_authenticate(user=self.user_a)
        
        # Add quality to dream
        response = self.client.put(f'/api/dreams/{self.dream_a.pk}/qualities/{self.quality_a.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check frequency updated
        self.quality_a.refresh_from_db()
        self.assertEqual(self.quality_a.frequency, 1)
        
        # Remove quality from dream
        response = self.client.delete(f'/api/dreams/{self.dream_a.pk}/qualities/{self.quality_a.pk}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Quality should be deleted since frequency is 0
        self.assertFalse(Quality.objects.filter(pk=self.quality_a.pk).exists())
