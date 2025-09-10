import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import axios from "axios";
import { Toaster } from "./components/ui/sonner";
import { toast } from "sonner";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "./components/ui/dialog";
import { Label } from "./components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Search, Plus, Car, CheckCircle, XCircle, Edit, Trash2, BarChart3, Upload, Camera, FileText, LogOut, Users, Settings, History, Archive, Calendar } from "lucide-react";
import Login from "./components/Login";
import UserManagement from "./components/UserManagement";
import HistoryComponent from "./components/History";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  // Authentication state
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [authToken, setAuthToken] = useState(null);
  const [currentTab, setCurrentTab] = useState('inventory');

  // Existing state
  const [cars, setCars] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [consignmentFilter, setConsignmentFilter] = useState("all");
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showCSVDialog, setShowCSVDialog] = useState(false);
  const [showPhotoDialog, setShowPhotoDialog] = useState(false);
  const [editingCar, setEditingCar] = useState(null);
  const [markingPresentCar, setMarkingPresentCar] = useState(null);
  const [csvFile, setCsvFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [carPhoto, setCarPhoto] = useState(null);
  const [vinPhoto, setVinPhoto] = useState(null);
  const carPhotoRef = useRef(null);
  const vinPhotoRef = useRef(null);
  
  // Archive-related state
  const [archives, setArchives] = useState([]);
  const [availableMonths, setAvailableMonths] = useState([]);
  const [selectedMonth, setSelectedMonth] = useState(null);
  const [selectedYear, setSelectedYear] = useState(null);
  const [showArchiveDialog, setShowArchiveDialog] = useState(false);
  const [archiveFormData, setArchiveFormData] = useState({
    archive_name: "",
    month: new Date().getMonth() + 1,
    year: new Date().getFullYear()
  });
  const [formData, setFormData] = useState({
    make: "",
    model: "",
    number: "",
    purchase_date: "",
    image_url: "",
    vin: "",
    is_consignment: false
  });

  // Check for existing authentication on component mount
  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    const userData = localStorage.getItem('user_data');
    
    if (token && userData) {
      try {
        const parsedUser = JSON.parse(userData);
        setAuthToken(token);
        setUser(parsedUser);
        setIsAuthenticated(true);
        
        // Set default axios header
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      } catch (error) {
        console.error('Error parsing user data:', error);
        handleLogout();
      }
    }
    setLoading(false);
  }, []);

  // Initialize data when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      const loadData = async () => {
        setLoading(true);
        await Promise.all([fetchCars(), fetchStats(), fetchAvailableMonths()]);
        if (currentTab === 'history') {
          await fetchArchives();
        }
        setLoading(false);
      };
      loadData();
    }
  }, [isAuthenticated, searchTerm, statusFilter, consignmentFilter, selectedMonth, selectedYear, currentTab]);

  // Handle login
  const handleLogin = (loginData) => {
    setAuthToken(loginData.access_token);
    setUser(loginData.user);
    setIsAuthenticated(true);
    
    // Set axios default header
    axios.defaults.headers.common['Authorization'] = `Bearer ${loginData.access_token}`;
  };

  // Handle logout
  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_data');
    delete axios.defaults.headers.common['Authorization'];
    setAuthToken(null);
    setUser(null);
    setIsAuthenticated(false);
    setCurrentTab('inventory');
  };

  // Show login screen if not authenticated
  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} />;
  }

  // Fetch cars from API
  const fetchCars = async () => {
    try {
      const params = new URLSearchParams();
      if (searchTerm) params.append('search', searchTerm);
      if (statusFilter && statusFilter !== 'all') params.append('status', statusFilter);
      if (consignmentFilter === 'consignment') params.append('is_consignment', 'true');
      if (consignmentFilter === 'regular') params.append('is_consignment', 'false');
      // Only add month/year filters if they are explicitly set (not null)
      // This allows showing all active cars when no specific month/year is selected
      if (selectedMonth && selectedYear) {
        params.append('month', selectedMonth);
        params.append('year', selectedYear);
      }
      
      const response = await axios.get(`${API}/cars?${params.toString()}`);
      setCars(response.data);
    } catch (error) {
      console.error('Error fetching cars:', error);
      toast.error('Failed to fetch cars');
    }
  };

  // Fetch inventory stats
  const fetchStats = async () => {
    try {
      const params = new URLSearchParams();
      // Only add month/year filters if they are explicitly set (not null)
      if (selectedMonth && selectedYear) {
        params.append('month', selectedMonth);
        params.append('year', selectedYear);
      }
      
      const response = await axios.get(`${API}/cars/stats/summary?${params.toString()}`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  // Fetch available months
  const fetchAvailableMonths = async () => {
    try {
      const response = await axios.get(`${API}/cars/available-months`);
      setAvailableMonths(response.data);
    } catch (error) {
      console.error('Error fetching available months:', error);
    }
  };

  // Fetch archives
  const fetchArchives = async () => {
    try {
      const response = await axios.get(`${API}/archives`);
      setArchives(response.data);
    } catch (error) {
      console.error('Error fetching archives:', error);
      toast.error('Failed to fetch archives');
    }
  };

  // Handle form submission for adding/editing cars
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const carData = {
        ...formData,
        number: formData.number,
        purchase_date: formData.purchase_date || null
      };

      if (editingCar) {
        await axios.put(`${API}/cars/${editingCar.id}`, carData);
        toast.success('Car updated successfully');
        setShowEditDialog(false);
        setEditingCar(null);
      } else {
        await axios.post(`${API}/cars`, carData);
        toast.success('Car added successfully');
        setShowAddDialog(false);
      }

      // Reset form and refresh data
      setFormData({ make: "", model: "", number: "", purchase_date: "", image_url: "", vin: "", is_consignment: false });
      await Promise.all([fetchCars(), fetchStats()]);
    } catch (error) {
      console.error('Error saving car:', error);
      toast.error('Failed to save car');
    }
  };

  // Handle CSV upload
  const handleCSVUpload = async () => {
    console.log('CSV Upload started, csvFile:', csvFile);
    
    if (!csvFile) {
      toast.error('Please select a CSV file');
      return;
    }

    // Validate file type
    if (!csvFile.name.toLowerCase().endsWith('.csv')) {
      toast.error('Please select a valid CSV file');
      return;
    }

    // Validate file size (max 5MB)
    if (csvFile.size > 5 * 1024 * 1024) {
      toast.error('File size must be less than 5MB');
      return;
    }

    setUploading(true);
    
    try {
      console.log('Creating FormData...');
      const formData = new FormData();
      formData.append('file', csvFile);

      console.log('Uploading CSV file:', csvFile.name, 'Size:', csvFile.size, 'Type:', csvFile.type);
      console.log('API endpoint:', `${API}/cars/import-csv`);
      
      const response = await axios.post(`${API}/cars/import-csv`, formData, {
        headers: {
          // Let axios set Content-Type automatically for multipart/form-data
        },
        timeout: 30000, // 30 second timeout
      });

      console.log('CSV upload response status:', response.status);
      console.log('CSV upload response data:', response.data);

      const result = response.data;
      
      if (result.success) {
        // Show detailed success message with import and update counts
        const total_processed = result.imported_count + (result.updated_count || 0);
        if (result.updated_count > 0) {
          toast.success(`${total_processed} Fahrzeuge verarbeitet: ${result.imported_count} neu importiert, ${result.updated_count} aktualisiert`);
        } else {
          toast.success(`${result.imported_count} Fahrzeuge erfolgreich importiert`);
        }
        
        if (result.errors && result.errors.length > 0) {
          console.warn('Import errors:', result.errors);
          toast.warning(`${result.errors.length} Zeilen hatten Fehler - Details in der Konsole`);
          // Show first few errors in console
          result.errors.forEach((error, index) => {
            if (index < 3) console.error(`Import Fehler ${index + 1}:`, error);
          });
        }
      } else {
        toast.error('Import fehlgeschlagen: ' + (result.message || 'Unbekannter Fehler'));
      }

      setShowCSVDialog(false);
      setCsvFile(null);
      
      console.log('Refreshing car list and stats...');
      await Promise.all([fetchCars(), fetchStats()]);
      console.log('Refresh completed');
      
    } catch (error) {
      console.error('CSV upload error:', error);
      console.error('Error details:', {
        message: error.message,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        headers: error.response?.headers
      });
      
      let errorMessage = 'Failed to upload CSV file';
      
      if (error.response?.status === 400) {
        errorMessage = error.response.data?.detail || 'Invalid CSV format or data';
      } else if (error.response?.status === 500) {
        errorMessage = 'Server error processing CSV';
      } else if (error.code === 'ECONNABORTED') {
        errorMessage = 'Upload timeout - file may be too large';
      } else if (error.message) {
        errorMessage += ': ' + error.message;
      }
      
      toast.error(errorMessage);
    } finally {
      setUploading(false);
    }
  };

  // Convert file to base64
  const fileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result.split(',')[1]); // Remove data:image/jpeg;base64, prefix
      reader.onerror = error => reject(error);
    });
  };

  // Handle photo capture for car photo
  const handleCarPhotoCapture = async (e) => {
    const file = e.target.files[0];
    if (file) {
      try {
        const base64 = await fileToBase64(file);
        setCarPhoto(base64);
      } catch (error) {
        toast.error('Failed to process car photo');
      }
    }
  };

  // Handle photo capture for VIN photo
  const handleVinPhotoCapture = async (e) => {
    const file = e.target.files[0];
    if (file) {
      try {
        const base64 = await fileToBase64(file);
        setVinPhoto(base64);
      } catch (error) {
        toast.error('Failed to process VIN photo');
      }
    }
  };

  // Handle marking car as present with photos
  const handleMarkPresent = async () => {
    if (!carPhoto || !vinPhoto) {
      toast.error('Both car photo and VIN photo are required');
      return;
    }

    try {
      await axios.patch(`${API}/cars/${markingPresentCar.id}/status`, {
        status: 'present',
        car_photo: carPhoto,
        vin_photo: vinPhoto
      });
      
      toast.success('Car marked as present with photo verification');
      setShowPhotoDialog(false);
      setMarkingPresentCar(null);
      setCarPhoto(null);
      setVinPhoto(null);
      await Promise.all([fetchCars(), fetchStats()]);
    } catch (error) {
      console.error('Error updating status:', error);
      toast.error('Failed to update car status');
    }
  };

  // Handle status toggle - simplified for marking absent, opens photo dialog for present
  const toggleCarStatus = async (car) => {
    if (car.status === 'present') {
      // Mark as absent (no photos needed)
      try {
        await axios.patch(`${API}/cars/${car.id}/status`, { status: 'absent' });
        toast.success('Car marked as absent');
        await Promise.all([fetchCars(), fetchStats()]);
      } catch (error) {
        console.error('Error updating status:', error);
        toast.error('Failed to update status');
      }
    } else {
      // Mark as present (requires photos)
      setMarkingPresentCar(car);
      setShowPhotoDialog(true);
      setCarPhoto(null);
      setVinPhoto(null);
    }
  };

  // Handle car deletion (admin only)
  const deleteCar = async (carId) => {
    if (!window.confirm('Möchten Sie dieses Fahrzeug wirklich löschen?')) return;
    
    try {
      await axios.delete(`${API}/cars/${carId}`);
      toast.success('Fahrzeug erfolgreich gelöscht');
      await Promise.all([fetchCars(), fetchStats()]);
    } catch (error) {
      console.error('Error deleting car:', error);
      toast.error('Fehler beim Löschen: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Handle delete all cars (admin only)
  const deleteAllCars = async () => {
    const confirmed = window.confirm(
      '⚠️ ACHTUNG: Möchten Sie wirklich ALLE Fahrzeuge löschen?\n\nDiese Aktion kann nicht rückgängig gemacht werden!'
    );
    
    if (!confirmed) return;
    
    const confirmation = prompt('Zur Bestätigung tippen Sie: ALLE LÖSCHEN');
    if (confirmation !== 'ALLE LÖSCHEN') {
      toast.error('Löschung abgebrochen - falsche Bestätigung');
      return;
    }

    try {
      const response = await axios.delete(`${API}/cars`);
      const result = response.data;
      toast.success(`Alle ${result.deleted_count} Fahrzeuge wurden gelöscht`);
      await Promise.all([fetchCars(), fetchStats(), fetchAvailableMonths()]);
    } catch (error) {
      console.error('Error deleting all cars:', error);
      toast.error('Fehler beim Löschen aller Fahrzeuge: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Handle monthly archive creation (admin only)
  const createMonthlyArchive = async () => {
    if (!archiveFormData.archive_name.trim()) {
      toast.error('Bitte geben Sie einen Archiv-Namen ein');
      return;
    }

    try {
      const response = await axios.post(`${API}/archives/create-monthly`, archiveFormData);
      const result = response.data;
      toast.success(`Archiv "${result.archive_name}" erfolgreich erstellt`);
      setShowArchiveDialog(false);
      setArchiveFormData({
        archive_name: "",
        month: new Date().getMonth() + 1,
        year: new Date().getFullYear()
      });
      
      // Refresh data
      await Promise.all([fetchCars(), fetchStats(), fetchAvailableMonths(), fetchArchives()]);
    } catch (error) {
      console.error('Error creating archive:', error);
      toast.error('Fehler beim Erstellen des Archivs: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Open edit dialog
  const openEditDialog = (car) => {
    setEditingCar(car);
    setFormData({
      make: car.make,
      model: car.model,
      number: car.number,
      purchase_date: car.purchase_date || "",
      image_url: car.image_url || "",
      vin: car.vin || "",
      is_consignment: car.is_consignment || false
    });
    setShowEditDialog(true);
  };

  const resetForm = () => {
    setFormData({ make: "", model: "", number: "", purchase_date: "", image_url: "", vin: "", is_consignment: false });
    setEditingCar(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 px-2 sm:px-4 lg:px-8">
      <div className="container mx-auto py-4 sm:py-8">
        {/* Header with User Info */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6 sm:mb-8">
          <div>
            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-slate-800 mb-2 flex items-center gap-2 sm:gap-3">
              <Car className="w-6 h-6 sm:w-8 sm:h-8 lg:w-10 lg:h-10 text-blue-600" />
              Dealership Inventory
            </h1>
            <p className="text-sm sm:text-base text-slate-600">Fahrzeug-Inventarsystem mit Foto-Verifizierung</p>
          </div>
          
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-4 w-full sm:w-auto">
            <div className="text-left sm:text-right">
              <p className="font-semibold text-slate-800">{user.username}</p>
              <p className="text-xs sm:text-sm text-slate-600">
                {user.role === 'admin' ? 'Administrator' : 'Benutzer'}
              </p>
            </div>
            <Button variant="outline" onClick={handleLogout} size="sm" className="w-full sm:w-auto">
              <LogOut className="w-4 h-4 mr-2" />
              Abmelden
            </Button>
          </div>
        </div>

        {/* Navigation Tabs */}
        <Tabs value={currentTab} onValueChange={setCurrentTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3 mb-8">
            <TabsTrigger value="inventory" className="flex items-center gap-2">
              <Car className="w-4 h-4" />
              Inventar
            </TabsTrigger>
            <TabsTrigger value="history" className="flex items-center gap-2">
              <History className="w-4 h-4" />
              Historie
            </TabsTrigger>
            {user.role === 'admin' && (
              <TabsTrigger value="users" className="flex items-center gap-2">
                <Users className="w-4 h-4" />
                Benutzerverwaltung
              </TabsTrigger>
            )}
          </TabsList>

          {/* Inventory Tab */}
          <TabsContent value="inventory">
            {/* Stats Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 sm:gap-4 lg:gap-6 mb-6 sm:mb-8">
              <Card className="hover:shadow-md transition-shadow">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-xs sm:text-sm font-medium text-gray-600">Eigene Fahrzeuge</CardTitle>
                  <BarChart3 className="h-3 w-3 sm:h-4 sm:w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="text-lg sm:text-2xl font-bold text-slate-800">{stats.regular_cars || 0}</div>
                </CardContent>
              </Card>
              
              <Card className="hover:shadow-md transition-shadow">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-xs sm:text-sm font-medium text-gray-600">Anwesend</CardTitle>
                  <CheckCircle className="h-3 w-3 sm:h-4 sm:w-4 text-green-600" />
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="text-lg sm:text-2xl font-bold text-green-600">{stats.present_cars || 0}</div>
                </CardContent>
              </Card>
              
              <Card className="hover:shadow-md transition-shadow">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-xs sm:text-sm font-medium text-gray-600">Abwesend</CardTitle>
                  <XCircle className="h-3 w-3 sm:h-4 sm:w-4 text-red-600" />
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="text-lg sm:text-2xl font-bold text-red-600">{stats.absent_cars || 0}</div>
                </CardContent>
              </Card>
              
              <Card className="hover:shadow-md transition-shadow">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-xs sm:text-sm font-medium text-gray-600">Konsignationen</CardTitle>
                  <Car className="h-3 w-3 sm:h-4 sm:w-4 text-blue-600" />
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="text-lg sm:text-2xl font-bold text-blue-600">{stats.consignment_cars || 0}</div>
                </CardContent>
              </Card>
              
              <Card className="hover:shadow-md transition-shadow col-span-2 sm:col-span-1">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-xs sm:text-sm font-medium text-gray-600">Anwesend %</CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="text-lg sm:text-2xl font-bold text-slate-800">{stats.present_percentage || 0}%</div>
                </CardContent>
              </Card>
            </div>

            {/* Rest of the existing inventory interface */}
            {/* Search and Filters */}
            <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 mb-6 sm:mb-8">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <Input
                    placeholder="Fahrzeuge suchen (Marke, Modell, VIN, Nummer)..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10 h-10 sm:h-11"
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-2 sm:flex gap-2 sm:gap-3">
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-full sm:w-[160px] lg:w-[180px] h-10 sm:h-11 lg:h-10">
                    <SelectValue placeholder="Status Filter" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Alle Status</SelectItem>
                    <SelectItem value="present">Anwesend</SelectItem>
                    <SelectItem value="absent">Abwesend</SelectItem>
                  </SelectContent>
                </Select>
                
                <Select value={consignmentFilter} onValueChange={setConsignmentFilter}>
                  <SelectTrigger className="w-full sm:w-[160px] lg:w-[180px] h-10 sm:h-11 lg:h-10">
                    <SelectValue placeholder="Fahrzeugtyp" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Alle Fahrzeuge</SelectItem>
                    <SelectItem value="regular">Eigene Fahrzeuge</SelectItem>
                    <SelectItem value="consignment">Konsignationen</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* CSV Upload Dialog */}
              <Dialog open={showCSVDialog} onOpenChange={setShowCSVDialog}>
                <DialogTrigger asChild>
                  <Button variant="outline" className="w-full sm:w-auto h-10 sm:h-11 lg:h-10">
                    <Upload className="w-4 h-4 mr-2" />
                    <span className="hidden sm:inline">CSV Import</span>
                    <span className="sm:hidden">Import</span>
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>CSV-Datei mit Spalten importieren</DialogTitle>
                    <DialogDescription>
                      CSV-Datei mit Spalten: make, model, number, purchase_date (optional), vin (optional), image_url (optional)
                      <br />Alle importierten Fahrzeuge werden als "abwesend" markiert.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="py-4">
                    <Label htmlFor="csv-file">CSV-Datei auswählen</Label>
                    <Input
                      id="csv-file"
                      type="file"
                      accept=".csv"
                      onChange={(e) => setCsvFile(e.target.files[0])}
                      className="mt-2"
                    />
                    {csvFile && (
                      <p className="text-sm text-gray-600 mt-2">
                        Ausgewählt: {csvFile.name}
                      </p>
                    )}
                  </div>
                  <DialogFooter>
                    <Button onClick={handleCSVUpload} disabled={!csvFile || uploading}>
                      {uploading ? 'Wird hochgeladen...' : 'Fahrzeuge importieren'}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>

              <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
                <DialogContent className="sm:max-w-[500px] max-h-[90vh] overflow-y-auto">
                  <DialogHeader>
                    <DialogTitle className="text-lg sm:text-xl">Neues Fahrzeug hinzufügen</DialogTitle>
                    <DialogDescription className="text-sm sm:text-base">Neues Fahrzeug zum Inventar hinzufügen (wird als abwesend markiert)</DialogDescription>
                  </DialogHeader>
                  <form onSubmit={handleSubmit}>
                    <div className="grid gap-4 py-4">
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                          <Label htmlFor="make" className="text-sm font-medium">Marke</Label>
                          <Input
                            id="make"
                            required
                            value={formData.make}
                            onChange={(e) => setFormData({...formData, make: e.target.value})}
                            className="h-11 sm:h-10 text-sm sm:text-base"
                          />
                        </div>
                        <div>
                          <Label htmlFor="model" className="text-sm font-medium">Modell</Label>
                          <Input
                            id="model"
                            required
                            value={formData.model}
                            onChange={(e) => setFormData({...formData, model: e.target.value})}
                            className="h-11 sm:h-10 text-sm sm:text-base"
                          />
                        </div>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                          <Label htmlFor="number" className="text-sm font-medium">Nummer</Label>
                          <Input
                            id="number"
                            required
                            value={formData.number}
                            onChange={(e) => setFormData({...formData, number: e.target.value})}
                            className="h-11 sm:h-10 text-sm sm:text-base"
                          />
                        </div>
                        <div>
                          <Label htmlFor="purchase_date" className="text-sm font-medium">Einkaufsdatum</Label>
                          <Input
                            id="purchase_date"
                            type="date"
                            value={formData.purchase_date}
                            onChange={(e) => setFormData({...formData, purchase_date: e.target.value})}
                            className="h-11 sm:h-10 text-sm sm:text-base"
                          />
                        </div>
                      </div>
                      <div>
                        <Label htmlFor="vin" className="text-sm font-medium">VIN</Label>
                        <Input
                          id="vin"
                          value={formData.vin}
                          onChange={(e) => setFormData({...formData, vin: e.target.value})}
                          className="h-11 sm:h-10 text-sm sm:text-base"
                        />
                      </div>
                      <div>
                        <Label htmlFor="image_url" className="text-sm font-medium">Bild-URL</Label>
                        <Input
                          id="image_url"
                          type="url"
                          value={formData.image_url}
                          onChange={(e) => setFormData({...formData, image_url: e.target.value})}
                          className="h-11 sm:h-10 text-sm sm:text-base"
                        />
                      </div>
                      
                      <div className="flex items-center space-x-3 p-3 bg-blue-50 rounded-lg">
                        <input
                          id="is_consignment"
                          type="checkbox"
                          checked={formData.is_consignment}
                          onChange={(e) => setFormData({...formData, is_consignment: e.target.checked})}
                          className="w-5 h-5 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2"
                        />
                        <Label htmlFor="is_consignment" className="text-sm font-medium text-gray-900 cursor-pointer">
                          Konsignations-Fahrzeug (gehört nicht uns)
                        </Label>
                      </div>
                    </div>
                    <DialogFooter>
                      <Button type="submit" className="w-full h-12 sm:h-11 lg:h-10 text-sm sm:text-base">Fahrzeug hinzufügen</Button>
                    </DialogFooter>
                  </form>
                </DialogContent>
              </Dialog>
            </div>

            {/* Action Buttons - Desktop-optimiert */}
            <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 mb-6 sm:mb-8">
              <Button onClick={() => setShowAddDialog(true)} className="h-11 sm:h-10 lg:h-9">
                <Plus className="w-4 h-4 mr-2" />
                <span>Fahrzeug hinzufügen</span>
              </Button>
              
              {user.role === 'admin' && cars.length > 0 && (
                <Button
                  onClick={deleteAllCars}
                  variant="destructive"
                  className="h-11 sm:h-10 lg:h-9"
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  <span>Alle löschen</span>
                </Button>
              )}
            </div>

            {/* Rest of the cars grid and dialogs - keeping existing code */}
            {/* Cars Grid - 3 Fahrzeuge pro Reihe auf Desktop/Tablet */}
            {loading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 sm:h-12 sm:w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-sm sm:text-base text-gray-600">Wird geladen...</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
                {cars.map((car) => {
                  // Use verification photo if car is present and has car_photo, otherwise use image_url
                  const displayImage = car.status === 'present' && car.car_photo 
                    ? `data:image/jpeg;base64,${car.car_photo}` 
                    : car.image_url;
                  
                  const isVerificationPhoto = car.status === 'present' && car.car_photo;
                  
                  return (
                    <Card key={car.id} className="overflow-hidden hover:shadow-lg transition-shadow">
                      {displayImage && (
                        <div className="h-36 sm:h-48 bg-gray-200 overflow-hidden relative">
                          <img
                            src={displayImage}
                            alt={`${car.make} ${car.model}`}
                            className="w-full h-full object-cover"
                            onError={(e) => {
                              e.target.style.display = 'none';
                            }}
                          />
                          {isVerificationPhoto && (
                            <div className="absolute top-1 sm:top-2 left-1 sm:left-2 bg-green-600 text-white px-1 sm:px-2 py-0.5 sm:py-1 rounded-full text-xs flex items-center gap-1">
                              <Camera className="w-2 h-2 sm:w-3 sm:h-3" />
                              <span className="hidden sm:inline">Verified</span>
                              <span className="sm:hidden">✓</span>
                            </div>
                          )}
                          {car.status === 'present' && car.vin_photo && (
                            <button
                              onClick={() => {
                                // Show VIN photo in a modal or new tab
                                const vinImage = `data:image/jpeg;base64,${car.vin_photo}`;
                                const newWindow = window.open();
                                newWindow.document.write(`
                                  <html>
                                    <head><title>VIN Verification - ${car.make} ${car.model}</title></head>
                                    <body style="margin:0; display:flex; justify-content:center; align-items:center; min-height:100vh; background:#000;">
                                      <img src="${vinImage}" style="max-width:100%; max-height:100%; object-fit:contain;" alt="VIN Verification Photo" />
                                    </body>
                                  </html>
                                `);
                              }}
                              className="absolute top-1 sm:top-2 right-1 sm:right-2 bg-blue-600 text-white p-0.5 sm:p-1 rounded-full hover:bg-blue-700 transition-colors"
                              title="VIN-Foto anzeigen"
                            >
                              <FileText className="w-2 h-2 sm:w-3 sm:h-3" />
                            </button>
                          )}
                        </div>
                      )}
                      <CardHeader className="p-3 sm:p-6">
                        <div className="flex justify-between items-start">
                          <div className="flex-1 min-w-0">
                            <CardTitle className="text-base sm:text-lg truncate">{car.make} {car.model}</CardTitle>
                            <CardDescription className="text-sm">Nr. {car.number}</CardDescription>
                          </div>
                          <div className="flex flex-col gap-1 ml-2">
                            <Badge variant={car.status === 'present' ? 'default' : 'destructive'} className="text-xs">
                              <span className="hidden sm:inline">{car.status === 'present' ? 'Anwesend' : 'Abwesend'}</span>
                              <span className="sm:hidden">{car.status === 'present' ? 'Da' : 'Weg'}</span>
                              {car.status === 'present' && car.car_photo && (
                                <Camera className="w-2 h-2 sm:w-3 sm:h-3 ml-1" title="Foto verifiziert" />
                              )}
                            </Badge>
                            {car.is_consignment && (
                              <Badge variant="secondary" className="text-xs bg-blue-100 text-blue-800">
                                <span className="hidden sm:inline">Konsignation</span>
                                <span className="sm:hidden">Kons.</span>
                              </Badge>
                            )}
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent className="p-3 sm:p-6 pt-0">
                        <div className="space-y-2">
                          {car.purchase_date && (
                            <p className="text-sm sm:text-base font-semibold text-blue-600">
                              <span className="hidden sm:inline">Eingekauft: </span>
                              <span className="sm:hidden">Gekauft: </span>
                              {new Date(car.purchase_date).toLocaleDateString('de-DE')}
                            </p>
                          )}
                          {car.vin && (
                            <p className="text-xs sm:text-sm text-gray-600 truncate">
                              VIN: {car.vin}
                            </p>
                          )}
                          <div className="flex flex-col sm:flex-row gap-2 pt-3 sm:pt-4">
                            <Button
                              size="sm"
                              variant={car.status === 'present' ? 'destructive' : 'default'}
                              onClick={() => toggleCarStatus(car)}
                              className="flex-1 text-xs sm:text-sm h-8 sm:h-9 lg:h-8"
                            >
                              {car.status === 'present' ? (
                                <>
                                  <XCircle className="w-3 h-3 sm:w-4 sm:h-4 mr-1" />
                                  <span className="hidden sm:inline">Als abwesend markieren</span>
                                  <span className="sm:hidden">Abwesend</span>
                                </>
                              ) : (
                                <>
                                  <CheckCircle className="w-3 h-3 sm:w-4 sm:h-4 mr-1" />
                                  <span className="hidden sm:inline">Als anwesend markieren</span>
                                  <span className="sm:hidden">Anwesend</span>
                                </>
                              )}
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => openEditDialog(car)}
                              className="text-xs sm:text-sm h-8 sm:h-9 lg:h-8 w-full sm:w-auto lg:w-auto"
                            >
                              <Edit className="w-3 h-3 sm:w-4 sm:h-4 mr-1" />
                              <span className="hidden sm:inline">Bearbeiten</span>
                              <span className="sm:hidden">Edit</span>
                            </Button>
                            
                            {/* Delete button only for admins */}
                            {user.role === 'admin' && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => deleteCar(car.id)}
                                className="text-red-600 hover:text-red-700 hover:bg-red-50 text-xs sm:text-sm h-8 sm:h-9 lg:h-8 w-full sm:w-auto lg:w-auto"
                              >
                                <Trash2 className="w-3 h-3 sm:w-4 sm:h-4 mr-1" />
                                <span className="hidden sm:inline">Löschen</span>
                                <span className="sm:hidden">Del</span>
                              </Button>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}

            {/* Photo Verification Dialog */}
            <Dialog open={showPhotoDialog} onOpenChange={setShowPhotoDialog}>
              <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle className="text-lg sm:text-xl">Fahrzeug als anwesend markieren</DialogTitle>
                  <DialogDescription className="text-sm sm:text-base">
                    Bitte nehmen Sie ein Foto des Fahrzeugs und der VIN-Nummer auf, um die Anwesenheit zu bestätigen.
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 sm:gap-6 py-4">
                  {/* Car Photo */}
                  <div>
                    <Label className="text-sm sm:text-base font-medium">Fahrzeug-Foto</Label>
                    <div className="mt-2 space-y-3">
                      <Button
                        variant="outline"
                        onClick={() => carPhotoRef.current?.click()}
                        className="w-full h-12 sm:h-11 text-sm sm:text-base"
                      >
                        <Camera className="w-4 h-4 sm:w-5 sm:h-5 mr-2" />
                        {carPhoto ? 'Fahrzeug-Foto aufgenommen ✓' : 'Fahrzeug-Foto aufnehmen'}
                      </Button>
                      <input
                        ref={carPhotoRef}
                        type="file"
                        accept="image/*"
                        capture="environment"
                        onChange={handleCarPhotoCapture}
                        className="hidden"
                      />
                      {carPhoto && (
                        <div className="w-full h-24 sm:h-32 bg-green-50 border-2 border-green-200 rounded flex items-center justify-center">
                          <CheckCircle className="w-6 h-6 sm:w-8 sm:h-8 text-green-600" />
                          <span className="ml-2 text-sm sm:text-base text-green-700">Fahrzeug-Foto aufgenommen</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* VIN Photo */}
                  <div>
                    <Label className="text-sm sm:text-base font-medium">VIN-Foto</Label>
                    <div className="mt-2 space-y-3">
                      <Button
                        variant="outline"
                        onClick={() => vinPhotoRef.current?.click()}
                        className="w-full h-12 sm:h-11 text-sm sm:text-base"
                      >
                        <FileText className="w-4 h-4 sm:w-5 sm:h-5 mr-2" />
                        {vinPhoto ? 'VIN-Foto aufgenommen ✓' : 'VIN-Foto aufnehmen'}
                      </Button>
                      <input
                        ref={vinPhotoRef}
                        type="file"
                        accept="image/*"
                        capture="environment"
                        onChange={handleVinPhotoCapture}
                        className="hidden"
                      />
                      {vinPhoto && (
                        <div className="w-full h-24 sm:h-32 bg-green-50 border-2 border-green-200 rounded flex items-center justify-center">
                          <CheckCircle className="w-6 h-6 sm:w-8 sm:h-8 text-green-600" />
                          <span className="ml-2 text-sm sm:text-base text-green-700">VIN-Foto aufgenommen</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
                <DialogFooter>
                  <Button
                    onClick={handleMarkPresent}
                    disabled={!carPhoto || !vinPhoto}
                    className="w-full h-12 sm:h-11 lg:h-10 text-sm sm:text-base"
                  >
                    Als anwesend markieren
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>

            {/* Edit Dialog */}
            <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
              <DialogContent className="sm:max-w-[500px] max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle className="text-lg sm:text-xl">Fahrzeug bearbeiten</DialogTitle>
                  <DialogDescription className="text-sm sm:text-base">Fahrzeug-Informationen aktualisieren</DialogDescription>
                </DialogHeader>
                <form onSubmit={handleSubmit}>
                  <div className="grid gap-4 py-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="edit-make" className="text-sm font-medium">Marke</Label>
                        <Input
                          id="edit-make"
                          required
                          value={formData.make}
                          onChange={(e) => setFormData({...formData, make: e.target.value})}
                          className="h-11 sm:h-10 text-sm sm:text-base"
                        />
                      </div>
                      <div>
                        <Label htmlFor="edit-model" className="text-sm font-medium">Modell</Label>
                        <Input
                          id="edit-model"
                          required
                          value={formData.model}
                          onChange={(e) => setFormData({...formData, model: e.target.value})}
                          className="h-11 sm:h-10 text-sm sm:text-base"
                        />
                      </div>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="edit-number" className="text-sm font-medium">Nummer</Label>
                        <Input
                          id="edit-number"
                          required
                          value={formData.number}
                          onChange={(e) => setFormData({...formData, number: e.target.value})}
                          className="h-11 sm:h-10 text-sm sm:text-base"
                        />
                      </div>
                      <div>
                        <Label htmlFor="edit-purchase_date" className="text-sm font-medium">Einkaufsdatum</Label>
                        <Input
                          id="edit-purchase_date"
                          type="date"
                          value={formData.purchase_date}
                          onChange={(e) => setFormData({...formData, purchase_date: e.target.value})}
                          className="h-11 sm:h-10 text-sm sm:text-base"
                        />
                      </div>
                    </div>
                    <div>
                      <Label htmlFor="edit-vin" className="text-sm font-medium">VIN</Label>
                      <Input
                        id="edit-vin"
                        value={formData.vin}
                        onChange={(e) => setFormData({...formData, vin: e.target.value})}
                        className="h-11 sm:h-10 text-sm sm:text-base"
                      />
                    </div>
                    <div>
                      <Label htmlFor="edit-image_url" className="text-sm font-medium">Bild-URL</Label>
                      <Input
                        id="edit-image_url"
                        type="url"
                        value={formData.image_url}
                        onChange={(e) => setFormData({...formData, image_url: e.target.value})}
                        className="h-11 sm:h-10 text-sm sm:text-base"
                      />
                    </div>
                    
                    <div className="flex items-center space-x-3 p-3 bg-blue-50 rounded-lg">
                      <input
                        id="edit_is_consignment"
                        type="checkbox"
                        checked={formData.is_consignment}
                        onChange={(e) => setFormData({...formData, is_consignment: e.target.checked})}
                        className="w-5 h-5 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2"
                      />
                      <Label htmlFor="edit_is_consignment" className="text-sm font-medium text-gray-900 cursor-pointer">
                        Konsignations-Fahrzeug (gehört nicht uns)
                      </Label>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button type="submit" className="w-full h-12 sm:h-11 lg:h-10 text-sm sm:text-base">Fahrzeug aktualisieren</Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>

            {cars.length === 0 && !loading && (
              <div className="text-center py-12 px-4">
                <Car className="w-12 h-12 sm:w-16 sm:h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-base sm:text-lg font-semibold text-gray-600 mb-2">Keine Fahrzeuge gefunden</h3>
                <p className="text-sm sm:text-base text-gray-500 mb-6">Beginnen Sie, indem Sie Fahrzeuge einzeln hinzufügen oder aus CSV importieren.</p>
                <div className="flex flex-col sm:flex-row justify-center gap-3 sm:gap-4 max-w-sm sm:max-w-none mx-auto">
                  <Button onClick={() => setShowAddDialog(true)} className="h-11 sm:h-10">
                    <Plus className="w-4 h-4 mr-2" />
                    <span className="hidden sm:inline">Erstes Fahrzeug hinzufügen</span>
                    <span className="sm:hidden">Fahrzeug hinzufügen</span>
                  </Button>
                  <Button variant="outline" onClick={() => setShowCSVDialog(true)} className="h-11 sm:h-10">
                    <Upload className="w-4 h-4 mr-2" />
                    CSV importieren
                  </Button>
                </div>
              </div>
            )}
          </TabsContent>

          {/* History Tab */}
          <TabsContent value="history">
            <HistoryComponent user={user} authToken={authToken} />
          </TabsContent>

          {/* User Management Tab (Admin only) */}
          {user.role === 'admin' && (
            <TabsContent value="users">
              <UserManagement token={authToken} />
            </TabsContent>
          )}
        </Tabs>
      </div>
      
      <Toaster />
    </div>
  );
}

export default App;